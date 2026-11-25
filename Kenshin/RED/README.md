# RED側プログラム

- `radicon_udp_server.py`：UDP 5005で操作指令を受信し、TCP 127.0.0.1:5000のSpresense姿勢角を使って直進保持・旋回を行う。
- `MotorControl.py`：BD6231モータードライバ制御。既存リポジトリの `for_raspberrypi/MotorControl.py` をコピー。

起動：
```bash
cd <Kenshin/REDを置いたディレクトリ>
python3 -B radicon_udp_server.py
```

必要条件：
- pigpio / pigpiod が動作していること
- モータードライバ配線がコード内のGPIO番号と一致していること
- SpresenseブリッジがTCP 5000で角度データを配信していること

このサーバーには50 cm位置推定走行コードは含まれません。Pi上の既存MotorControl.pyとの完全一致は未照合です。
