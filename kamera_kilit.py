import ctypes
import os
import sys
from ctypes import wintypes
from pathlib import Path
from time import monotonic, sleep

import cv2
import mediapipe as mp


KAMERA_NO = 0
KILIT_SURESI = 5
PENCERE = "Kamera kilidi testi - cikis icin Q"
DESKTOP_READOBJECTS = 0x0001
UOI_NAME = 2

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)

islem_oturumu = kernel32.ProcessIdToSessionId
islem_oturumu.argtypes = (wintypes.DWORD, wintypes.LPDWORD)
islem_oturumu.restype = wintypes.BOOL

konsol_oturumu = kernel32.WTSGetActiveConsoleSessionId
konsol_oturumu.argtypes = ()
konsol_oturumu.restype = wintypes.DWORD

giris_masaustunu_ac = user32.OpenInputDesktop
giris_masaustunu_ac.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
giris_masaustunu_ac.restype = wintypes.HANDLE

masaustu_bilgisi = user32.GetUserObjectInformationW
masaustu_bilgisi.argtypes = (
    wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD, wintypes.LPDWORD
)
masaustu_bilgisi.restype = wintypes.BOOL

masaustunu_kapat = user32.CloseDesktop
masaustunu_kapat.argtypes = (wintypes.HANDLE,)
masaustunu_kapat.restype = wintypes.BOOL

windows_kilitle = user32.LockWorkStation
windows_kilitle.argtypes = ()
windows_kilitle.restype = wintypes.BOOL


class KameraHatasi(RuntimeError):
    pass


def masaustu_etkin(oturum):
    # Ayrilmis bir oturumda OpenInputDesktop yine bir masaustu dondurebilir.
    if konsol_oturumu() != oturum:
        return False

    masaustu = giris_masaustunu_ac(0, False, DESKTOP_READOBJECTS)
    if not masaustu:
        return False

    try:
        ad = ctypes.create_unicode_buffer(256)
        if not masaustu_bilgisi(masaustu, UOI_NAME, ad, ctypes.sizeof(ad), None):
            return False
        return ad.value.casefold() == "default"
    finally:
        masaustunu_kapat(masaustu)


def kamerayi_izle(algilayici, oturum, arka_plan):
    """Masaustu degisirse kamerayi birakir, Q ile uygulamadan cikar."""
    kamera = cv2.VideoCapture(KAMERA_NO)
    kisi_goruldu = False
    bos_kalma_baslangici = None
    kilit_istendi = False

    try:
        if not kamera.isOpened():
            raise KameraHatasi(f"Kamera {KAMERA_NO} acilamadi.")

        while masaustu_etkin(oturum):
            okundu, kare = kamera.read()
            if not okundu:
                raise KameraHatasi("Kameradan goruntu alinamadi.")

            rgb = cv2.cvtColor(kare, cv2.COLOR_BGR2RGB)
            goruntu = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            kisi_var = bool(algilayici.detect(goruntu).pose_landmarks)

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
                if gecen_sure >= KILIT_SURESI:
                    if not kilit_istendi:
                        if not masaustu_etkin(oturum):
                            return True
                        if not windows_kilitle():
                            hata = ctypes.get_last_error()
                            if not masaustu_etkin(oturum):
                                return True
                            raise ctypes.WinError(hata)
                        kilit_istendi = True
                    durum = "Windows kilidi istendi"
                else:
                    durum = f"Kadraj bos: {gecen_sure:.1f} / {KILIT_SURESI} sn"

            if not arka_plan:
                renk = (0, 255, 0) if kisi_var else (0, 165, 255)
                cv2.putText(kare, durum, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, renk, 2)
                cv2.imshow(PENCERE, kare)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    return False

        return True
    finally:
        kamera.release()
        if not arka_plan:
            cv2.destroyAllWindows()


def main():
    arka_plan = "--arka-plan" in sys.argv
    oturum = wintypes.DWORD()
    if not islem_oturumu(os.getpid(), ctypes.byref(oturum)):
        raise ctypes.WinError(ctypes.get_last_error())

    model = Path(__file__).with_name("pose_landmarker_lite.task")
    if not model.is_file():
        raise SystemExit("Model dosyasi bulunamadi. Indirme komutunu kontrol et.")

    secenekler = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(model)),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
    )

    try:
        with mp.tasks.vision.PoseLandmarker.create_from_options(secenekler) as algilayici:
            while True:
                if not masaustu_etkin(oturum.value):
                    sleep(0.25)
                    continue

                try:
                    if not kamerayi_izle(algilayici, oturum.value, arka_plan):
                        break
                except KameraHatasi as hata:
                    if not arka_plan and masaustu_etkin(oturum.value):
                        raise SystemExit(str(hata)) from None
                    # Diger oturum kamerayi henuz serbest birakmamis olabilir.
                    sleep(1)
    except KeyboardInterrupt:
        if not arka_plan:
            print("Program durduruldu.")


if __name__ == "__main__":
    main()
