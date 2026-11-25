# Spresense v2 — RED2.0 実験・操作ガイド

> 2026-11-25 時点の実験構成メモ。**旧版 `for_pc/`・`for_raspberrypi/`・ルート README は変更せず保持**しています。

このフォルダは、RED2.0 の **Spresense IMUを使うラジコン制御、UWBアンカー、Motive、実験時だけのCSV保存**を一か所にまとめるためのものです。

## 最初に開くファイル

| ファイル | 内容 |
|---|---|
| [01_STARTUP.md](01_STARTUP.md) | **実験の起動順・停止・Windowsへのダウンロード** |
| [02_PORTS_AND_DATA.md](02_PORTS_AND_DATA.md) | **TCP/UDPポート・USBシリアル・CSV列・時刻同期** |
| [03_CODE_STATUS.md](03_CODE_STATUS.md) | **今の実機コードがどこにあるか／最新版をGitHubに移す手順** |
| [tools/record_csv.py](tools/record_csv.py) | **動作確認済みのSpresense CSV記録用Pythonコード** |

## 現在の構成

```text
Windows PC / Proコン
  procon_send.py
       | UDP 5005（操作指令）
       v
Raspberry Pi 192.168.1.247（2026-11-24 実験時）
  radicon_udp_server.py --imu （RED制御）
       | TCP localhost:5000 （IMUデータ）
       v
  pospredict_bridge.py  ---- USB CP2102N ---- Spresense MultiIMU
       |
       +-- TCP localhost:5000 --> record_csv.py --> ~/pospredict/logs/spresense_*.csv

  UWB測距プログラム -------- USB FTDI FT230X -------- UWBタグ/アンカー系

Motive（別PC）--> 剛体の位置・姿勢をCSV出力
```

**注意**：
- GitHub旧版の `for_raspberrypi/radicon_udp_server.py` は、実機の最新版 `~/Red2.0-Control-Software/explore_algorithm/radicon_udp_server.py` と同一だと確認できていません。**旧GitHub版を実機へコピーしない**でください。
- `pospredict_bridge.py` は研究室側にあるソフトで、このフォルダにはソースを複製していません。権利・公開可否を確認する必要があります。
- 現在のリポジトリは **public** です。研究の生データ・秘密情報・実験協力者の情報などは、公開許可を得るまでアップロードしないでください。
- USBポートやPiのIPは接続により変わりえます。起動前に確認してください。

## 確認済み事項

- 2026-11-24：`record_csv.py` で **1,212行**および **17,064行**のSpresense受信データを保存できた。
- `Ctrl+C` で記録が終了し、通常のラジコン制御とは独立してCSVを保存可能。
- 記録された時刻は **PiがTCPデータを受信した時刻**。Motiveとの厳密な同期には別途検証が必要。

## 今後の更新方針

1. 既存ファイルは残す。
2. 実機上で正常動作している最新版ラジコン／UWBプログラムを**先に回収**して照合する。
3. 最新版と確認したコードだけ、この `Spresense_v2/` 配下に追加する。
4. 旧版に影響させず、実験結果に応じて手順書を更新する。
