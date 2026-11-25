# Kenshin RED Controller

Nintendo Switch Pro Controller と Xbox 360 Controller から RED を操作するためのコードです。

## 構成

```text
Kenshin/
├── Kenshin/       # Nintendo Switch Pro Controller (Windows)
├── Xbox/          # Xbox 360 Controller (Windows)
├── RED/           # RED側 UDPサーバーとモーター制御依存
├── Spresense/     # Spresense TCPブリッジの起動情報
└── UWB/           # UWBとの分担・未確認事項
```

## 起動順

1. RED側で pigpio / pigpiod を利用可能にし、`RED/radicon_udp_server.py` を起動。
2. Spresenseの `pospredict_bridge.py` を起動し、TCP 5000で姿勢角を配信。
3. Windowsで `pygame` をインストールし、ProコンかXboxの送信スクリプトを**どちらか一方だけ**起動。

Windows：
```powershell
python -m pip install pygame
```

各送信スクリプト先頭の `RED_IP` を、RED上の `hostname -I` で確認した現在のIPに合わせてください。

## 制御内容

- 左スティック：押している間の連続移動・左右旋回。Spresense角度による直進方向保持。
- 5° / 45° / 90°旋回：角度を読みながら停止位置を調整。
- 50 cm位置推定走行：**削除済み**。50 cm走行コマンドは送信しません。Proコンの右スティックも未使用です。
- UDP指令が0.4秒途切れた場合、RED側で停止します。

## 2026-11-25の実験ログ

この日のログでは、5°旋回と45°旋回が表示上の許容誤差±0.50°以内でPASSしました。これはSpresense角度表示に対する制御ログであり、Motiveによる独立した精度検証ではありません。

## 注意

- 最初は車輪を浮かせて、停止・方向・ボタン割り当てを確認してください。
- UWB測距・アンカー処理はこのコントローラーサーバーとは別系統です。詳細は `UWB/README.md` を参照してください。
