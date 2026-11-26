# Kamera Kilit

USB kameranın görüş alanında bir kişi algılandıktan sonra kadraj
kesintisiz 3 saniye boş kalırsa Windows oturumunu kilitler.
Kamera görüntüsü bilgisayarda işlenir ve dosyaya kaydedilmez.

## Gereksinimler

- Windows (bilgisayarın yerel masaüstü oturumu)
- Python 3.13 (64 bit)
- Windows'un erişebildiği bir kamera

## Kurulum

Projeyi indirip klasöründe PowerShell aç. Ardından çalıştır:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task" -OutFile ".\pose_landmarker_lite.task"
```

## Kullanım

```powershell
.\.venv\Scripts\python.exe .\kamera_kilit.py
```

Kamera karşısına oturup `Kisi algilandi` yazısını bekle. Kadrajdan çık.
5 saniye içinde dönersen sayaç sıfırlanır. Kadraj boş kalırsa Windows
kilitlenir. Programdan çıkmak için görüntü penceresinde `Q` tuşuna bas.

Yanlış kamera açılırsa `kamera_test.py` ile kamera numaralarını dene.
Çalışan numarayı `kamera_kilit.py` dosyasının başındaki `KAMERA_NO`
değerine yaz. Kadrajda başka biri kalırsa sayaç başlamaz.

## Oturum açıldığında çalıştırma

Windows Görev Zamanlayıcı'da kendi kullanıcın için oturum açma tetikleyicisi
oluştur ve görevi yalnızca kullanıcı oturum açtığında çalışacak şekilde
ayarla. Program olarak proje klasöründeki `.venv\Scripts\pythonw.exe`
dosyasını seç. Bağımsız değişkenler alanına `kamera_kilit.py` dosyasının
tam yolunu çift tırnak içinde yaz ve sonuna `--arka-plan` ekle.

## Birden fazla Windows hesabı

Aynı bilgisayarda birden fazla hesap kullanıyorsan her hesapta projeyi
kur ve o hesap için ayrı bir oturum açma görevi oluştur. Var olan bir
kurulumu güncellerken görevi durdur, `kamera_kilit.py` dosyasını değiştir
ve görevi yeniden çalıştır.

**Kullanıcı değiştir** ile geçiş yaptığında önceki oturum kamerayı bırakır.
Etkin masaüstündeki görev kamerayı açar ve kilit sayacını başlatmadan önce
yeniden bir kişinin algılanmasını bekler. Ekran kilitliyken kamera bırakılır.
