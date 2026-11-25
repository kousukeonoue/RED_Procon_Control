# 02 — ポート・データ・時刻の一覧

2026-11-24 の実験時に分かっている情報。機器・ケーブル・Wi-Fiが変わった場合は**毎回確認**する。

## ネットワーク通信

| 通信 | 送信元 → 受信先 | ポート | 確認状況 |
|---|---|---|---|
| Proコン操作 | Windows `procon_send.py` → Pi `radicon_udp_server.py` | **UDP 5005** | 現行運用で使用 |
| Spresense IMU配信 | Pi `pospredict_bridge.py` → ラジコン側 | **TCP 5000** | 現行運用で使用 |
| Spresense IMU配信 | Pi `pospredict_bridge.py` → `record_csv.py` | **TCP 5000** | CSV保存で確認 |
| UWBタグ・アンカー | USBシリアル経由（別途アンカー側が関与） | 未確認 | 現行コード・起動引数を確認する |
| Motive | 専用PCで録画 | 未確認 | ネットワークストリームが必要なら別途確認 |

Pi IP：**192.168.1.247**（2026-11-24 の実験時）。過去のREADMEの `192.168.1.171` ではない。Wi-Fi環境に応じて変更される可能性がある。

## Raspberry PiのUSBシリアル

```bash
ls -l /dev/serial/by-id/
```

2026-11-24 の例：

| 機器 | `/dev/serial/by-id/` | その時のリンク先 |
|---|---|---|
| **Spresense側** | `usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_36e558692611e911b0e745ad87f8ef3e-if00-port0` | `/dev/ttyUSB1` |
| **UWB側** | `usb-FTDI_FT230X_Basic_UART_DM86TTWC-if00-port0` | `/dev/ttyUSB0` |

重要：`ttyUSB0` と `ttyUSB1` は物理ケーブルの接続順により入れ替わることがある。**機器名を検証し、by-idで指定**する。2つのソフトから同じUSBポートを同時に直接開かない。

## Spresense CSV

`~/pospredict/record_csv.py` はブリッジからTCPで受信し、実験時だけ以下に保存する：

```text
/home/red/pospredict/logs/spresense_YYYYMMDD_HHMMSS.csv
```

実際に確認できた列：

```csv
time,unix_ns,x,y,z,roll,yaw,pitch
2026-11-24T15:34:15.609+09:00,1795502055609358048,4.26,-1.24,4.15,0.44,-1.47,-101.11
```

| CSV列 | 由来 | 注意 |
|---|---|---|
| `time` | Raspberry Piが受け取ったローカル時刻（例 `+09:00`） | センサー内時刻ではない |
| `unix_ns` | Piでの受信Unix時刻（ns） | ナノ秒の桁数は**計時精度**の保証ではない |
| `x,y,z` | ブリッジ表示の `X,Y,Z` | 推定値。単位、座標原点、ドリフトは研究室ソースで確認 |
| `roll` | ブリッジ表示の `R` | 名前と物理軸の一致は要検証 |
| `yaw` | ブリッジ表示で2つ目の `Y` | 最初の `Y` は位置成分 |
| `pitch` | ブリッジ表示の `P` | **現在のRED旋回制御で使用している角度はこの `P`**。一般的なyawと混同しない |

このCSVは受信済みの**位置・姿勢推定値**で、加速度・角速度の生データやUWB CIRは含まれない。

実績：
- `spresense_20261124_153415.csv` — **1,212件**
- `spresense_20261124_154013.csv` — **17,064件**

過去のCSVはおよそ100Hzの受信が見られた。ただし通信・処理負荷でレートが変わるため、実験ごとに時刻差を検査する。

## UWBとMotiveのデータ

過去のUWBログ形式（一例）：

```csv
time,seq_cnt,nlos,distance,azimuth,azimuth_fom,elevation,elevation_fom,rssi,pdoa1,pdoa2
```

研究室のUWBコードで、使用する単位・アンカーID・測距開始時刻・CIR保存方法を確認すること。

過去のMotive剛体名の例：RED `kousuke`、アンカー `rintopi 002`。剛体名・座標系・原点（アンテナ位置とのオフセット）は**実験時の設定とCSVで再確認**する。

## 異なる装置を比較するとき

- Motive CSVとUWB CSV、Spresense CSVのタイムゾーン・時刻基準をそろえる。
- Spresenseの `time` はPiでのTCP受信時刻。Spresense内部サンプリング時刻やMotiveの時刻と同一とは限らない。
- 同じ時間帯の軌跡・角度を比較する前に、開始時刻、欠損、遅延、軸の向き、角度の定義を確認する。
- **絶対に `pitch` 列を名前だけで除外しない**。制御で用いた角度 `P` はこの列にある。
- アンカー距離、REDの遮蔽方向、Motiveの基準位置は実験の再現に必要なので同時に記録する。
