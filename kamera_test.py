import cv2

kamera_no = 0
kamera = cv2.VideoCapture(kamera_no)

try:
    if not kamera.isOpened():
        raise SystemExit(f"Kamera {kamera_no} acilamadi.")

    while True:
        okundu, kare = kamera.read()
        if not okundu:
            raise SystemExit("Kameradan goruntu alinamadi.")

        cv2.imshow("Kamera testi - cikis icin Q", kare)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    kamera.release()
    cv2.destroyAllWindows()