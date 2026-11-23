import sys
import ctypes
from ctypes import wintypes

from pathlib import Path
from time import monotonic


import cv2
import mediapipe as mp

windows_kilitle = ctypes.WinDLL("user32", use_last_error=True).LockWorkStation
windows_kilitle.argtypes = ()
windows_kilitle.restype = wintypes.BOOL

model = Path(__file__).with_name("pose_landmarker_lite.task")
if not model.is_file():
    raise SystemExit("Model dosyasi bulunamadi. Indirme komutunu kontrol et.")

secenekler = mp.tasks.vision.PoseLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=str(model)),
    running_mode=mp.tasks.vision.RunningMode.IMAGE,
)

arka_plan = "--arka-plan" in sys.argv
pencere = "Kamera kilidi testi - cikis icin Q"
kamera = cv2.VideoCapture(0)
kisi_goruldu = False
bos_kalma_baslangici = None
kilit_istendi = False

try:
    if not kamera.isOpened():
        raise SystemExit("Kamera 0 acilamadi.")

    with mp.tasks.vision.PoseLandmarker.create_from_options(secenekler) as algilayici:
        while True:
            okundu, kare = kamera.read()
            if not okundu:
                raise SystemExit("Kameradan goruntu alinamadi.")

            # Kameradan gelen karenin tamamini modele ver.
            rgb = cv2.cvtColor(kare, cv2.COLOR_BGR2RGB)
            goruntu = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            sonuc = algilayici.detect(goruntu)
            kisi_var = bool(sonuc.pose_landmarks)

            simdi = monotonic()
            if kisi_var:
                kisi_goruldu = True
                bos_kalma_baslangici = None
                kilit_istendi = False
                durum = "Kisi algilandi"
            elif not kisi_goruldu:
                durum = "Ilk kisi algilamasi bekleniyor"
            else:
                if bos_kalma_baslangici is None:
                    bos_kalma_baslangici = simdi

                gecen_sure = simdi - bos_kalma_baslangici
                if gecen_sure >= 5:
                    if not kilit_istendi:
                        if not windows_kilitle():
                            raise ctypes.WinError(ctypes.get_last_error())
                        kilit_istendi = True
                    durum = "Windows kilidi istendi"
                else:
                    durum = f"Kadraj bos: {gecen_sure:.1f} / 5 sn"

            if not arka_plan:
                renk = (0, 255, 0) if kisi_var else (0, 165, 255)
                cv2.putText(
                    kare, durum, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, renk, 2
                )
                cv2.imshow(pencere, kare)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
except KeyboardInterrupt:
    print("Program durduruldu.")
finally:
    kamera.release()
    cv2.destroyAllWindows()