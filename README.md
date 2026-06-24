# RED Pro Controller Control

## 概要

Nintendo Switch Pro Controller を PC に接続し、PC から UDP 通信で Raspberry Pi（RED）を操作する。

PC側でProコンの入力を読み取り、UDPでRED側に操作コマンドを送信する。

## 機能

* ラジコン操作
* リアルタイム映像配信
* 静止画保存

---

# 使用ファイル

## PC側

```text
for_pc/main/procon_send.py
for_pc/controller_check/procon_check.py
```

## RED側

```text
for_raspberrypi/radicon_udp_server.py
for_raspberrypi/Radicon.py
for_raspberrypi/MotorControl.py
for_raspberrypi/FloorLight.py
```

---

# IPアドレスについて

このREADMEでは、REDのIPアドレスを以下として説明する。

```text
192.168.1.171
```

別のREDを使う場合や、IPアドレスが変わった場合は、以下を変更する。

## PC側

`for_pc/main/procon_send.py` の中の `RED_IP` を変更する。

```python
RED_IP = "192.168.1.171"
```

## SSH接続・ブラウザ確認

README内の以下のIPアドレスも、使用するREDのIPアドレスに置き換える。

```text
ssh red@192.168.1.171
http://192.168.1.171:8080/?action=stream
http://192.168.1.171:8081
```

---

# ラジコン操作

## 1. RED側

PowerShell で RED に SSH 接続する。

```powershell
ssh red@192.168.1.171
```

RED側で UDP サーバーを起動する。

```bash
cd ~/Red2.0-Control-Software/explore_algorithm
python3 radicon_udp_server.py
```

起動確認

```text
UDP server start : port 5005
```

---

## 2. PC側

別の PowerShell で PC側の送信プログラムを起動する。

```powershell
cd "C:\Users\kousuke\Desktop\RED_Procon_Control\for_pc\main"
python procon_send.py
```

起動確認

```text
接続: Nintendo Switch Pro Controller
```

---

## 操作

```text
A      前進
B      後退
X      停止
Y      停止

左スティック
右スティック
→ 移動操作

L + R
→ 画像保存
```

---

# ライブ映像

別の PowerShell で RED に SSH 接続する。

```powershell
ssh red@192.168.1.171
```

mjpg-streamer のフォルダへ移動する。

```bash
cd ~/mjpg-streamer/mjpg-streamer-experimental
```

USBカメラで起動する場合

```bash
./mjpg_streamer -i "./input_uvc.so -d /dev/video1 -r 640x480 -f 15" -o "./output_http.so -w ./www -p 8080"
```

ブラウザで確認する。

```text
http://192.168.1.171:8080/?action=stream
```

---

# カメラ切り替え

USBカメラ

```text
/dev/video1
```

標準カメラ

```text
/dev/video0
```

標準カメラで起動する場合

```bash
./mjpg_streamer -i "./input_uvc.so -d /dev/video0 -r 640x480 -f 15" -o "./output_http.so -w ./www -p 8080"
```

---

# 静止画保存

条件

```text
1. ライブ配信中
2. radicon_udp_server.py 起動中
3. procon_send.py 起動中
```

その状態で

```text
L + R
```

を押す。

保存先

```text
/home/red/captures
```

---

# 保存画像を見る

別の PowerShell で RED に SSH 接続する。

```powershell
ssh red@192.168.1.171
```

保存先フォルダで簡易サーバーを起動する。

```bash
cd /home/red/captures
python3 -m http.server 8081
```

ブラウザで確認する。

```text
http://192.168.1.171:8081
```

保存した画像を確認できる。

---

# 停止

各画面で以下を押す。

```text
Ctrl + C
```

---


# REDの終了

SSH接続中に以下を実行する。

```bash
sudo shutdown -h now
```

REDの電源を消す
