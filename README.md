# Kraken Tester (KrakenKivyTestApp)

**Beginners:** For a full walkthrough (concepts, structure, data flow, and code), see **[BEGINNER_GUIDE.md](BEGINNER_GUIDE.md)**.

## Project kya hai?

Yeh app **Kraken** naam ke BLE (Bluetooth Low Energy) device ko **scan**, **connect**, aur **monitor** karne ke liye banaya gaya hai. Kraken ek hardware device hai jo pressure data aur BLE connection info bhejta hai. App in devices ko dhoondhta hai, unse connect hota hai, aur live data (RSSI, pressure, channel map, etc.) dikhata hai aur CSV mein log karta hai.

---

## Yeh kis cheez se bana hua hai? (Tech Stack)

| Cheez | Use |
|-------|-----|
| **Python 3.11** | Main language |
| **Kivy** | Mobile/desktop UI framework (touch-friendly, cross-platform) |
| **Bleak** | BLE (Bluetooth Low Energy) — scan, connect, GATT read/notify |
| **NumPy** | Data parsing (bytes → numbers) |
| **Pipenv** | Dependencies manage karne ke liye (Pipfile) |
| **Buildozer** | Android APK banane ke liye (Kivy + python-for-android) |

**Platforms:**
- **Desktop (Windows/Mac/Linux):** Python + Kivy se run ho sakta hai.
- **Android:** Buildozer se APK banti hai; `java/` folder mein BLE ke liye extra Java code (Bleak Android support) hai.

---

## Project structure (short)

```
KrakenKivyTestApp-main/
├── main.py              # App entry, Kivy AppRoot, BLE scan loop, tabs
├── Pipfile / Pipfile.lock   # Python dependencies (Pipenv)
├── buildozer.spec       # Android build config (buildozer)
├── .env                 # Env vars (if any)
├── python/
│   ├── ble_utils.py     # BLE scan — Kraken beacons dhoondhta hai
│   ├── kraken_uuids.py  # BLE service/characteristic UUIDs
│   ├── kraken_widget.py # Per-Kraken UI: connect, RSSI, pressure, BLE info
│   ├── sl_status_code_parser.py  # Disconnect reason codes
│   └── csv_log.py       # CSV logging (events + BLE connection data)
├── java/                # Android BLE (Bleak) — PythonBluetoothGattCallback, etc.
└── Tools/
    └── AndroidBuildLocal_WSL2.bat   # WSL2 se Android build script
```

---

## Kaise run karein?

### 1) Dependencies install karein

**Windows par** — agar `pip` recognize nahi hota, **Python 3.11** use karein (Kivy 3.14 par abhi theek se nahi chalta):

```powershell
py -3.11 -m pip install -r requirements.txt
```

**Pipenv use karna ho** (Windows):

```powershell
py -3.11 -m pip install pipenv
py -3.11 -m pipenv install
```

**Linux/Mac** — Python 3.11 ke saath:

```bash
pip install -r requirements.txt
# ya: pipenv install
```

### 2) Desktop par run karein

**Windows (Python 3.11):**

```powershell
py -3.11 main.py
```

Pipenv use kiya ho to:

```powershell
py -3.11 -m pipenv run python main.py
```

**Linux/Mac:**

```bash
python main.py
# ya: pipenv run python main.py
```

- App open hogi: **Dashboard** tab + har Kraken ke liye alag tab (jaise scan mein device mile).
- BLE scan har ~1 sec hota hai; naye Kraken range mein aate hi naya tab add hota hai.
- Data `Data/` folder (Windows par project ke saath) mein CSV files mein log hota hai.

**Note:**  
- **Windows:** Bluetooth on hona chahiye; Kraken devices range mein honi chahiye.  
- **Android:** App ko Bluetooth + Location permissions deni padti hain (code mein already request hai).

### 3) Android par run karein (APK banana)

- **Full steps:** **[ANDROID_BUILD.md](ANDROID_BUILD.md)** — WSL2 setup, dependencies, build, install on phone.
- **Buildozer** use hota hai; typically **Linux ya WSL2** par build kiya jata hai.
- `Tools/AndroidBuildLocal_WSL2.bat` WSL2 (e.g. Ubuntu-22.04) use karta hai: project copy karke WSL mein `buildozer android debug` chalaata hai, phir APK `LocalAndroidBuild` mein copy hoti hai.

WSL2 (Ubuntu) ke andar manually:

```bash
cd /path/to/KrakenKivyTestApp-main
pip install buildozer
buildozer -v android debug
```

APK `bin/` ke andar milegi, device par install karke run karein.

---

## Summary

- **Kya hai:** Kraken BLE devices ko scan/connect/monitor karne wala Kivy app.  
- **Kis mein bana:** Python 3.11, Kivy, Bleak, NumPy; Android ke liye Buildozer + Java (Bleak).  
- **Kaise run:** `pipenv install` → `pipenv run python main.py` (desktop); Android ke liye buildozer se APK banao.
