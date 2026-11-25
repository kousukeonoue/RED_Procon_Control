# 03 — 現行コードとGitHub保存状況

## 保存方針

- **旧コードはすべて残す。** リポジトリ直下の `for_pc/`、`for_raspberrypi/`、`README.md` を上書きしていない。
- 新しく確認した部分を `Spresense_v2/` の中に分離する。
- 現在のPiで動いている制御コードは **未取得**。動作中のプログラムを推測で復元して「最新版」として公開しない。
- 研究室が作ったSpresense関連ソフトは公開可否を確認してから収録。CSVの生データも研究室の規則を確認。

## コードの所在と確認状況

| 機能 | 現在の実機上で使用している場所 | このGitHubへの収録状況 |
|---|---|---|
| Proコン送信 | Windows `$HOME\Desktop\for_pc\main\procon_send.py` | **旧版のみ** `for_pc/main/procon_send.py`。現在のPC実体とは未照合 |
| REDラジコン/直進・旋回 | Pi `~/Red2.0-Control-Software/explore_algorithm/radicon_udp_server.py` | **旧版のみ** `for_raspberrypi/radicon_udp_server.py`。実機版は未回収 |
| 走行の下位依存 | Pi上の制御プロジェクト内 `Radicon.py`・`MotorControl.py` 等 | **旧版のみ**。現在の依存関係は未照合 |
| Spresenseブリッジ | Pi `~/pospredict/pospredict_bridge.py` | 研究室コードにつき未収録 |
| Spresense CSV記録 | Pi `~/pospredict/record_csv.py` | **今回使ったコード** `Spresense_v2/tools/record_csv.py` に追加 |
| UWB測距 | Pi `~/Red2.0-Control-Software/explore_algorithm/DS_TWR_SR150_Multisession2.py` 等 | 未回収・起動引数未確認 |
| アンカー側サーバー | 実機上で要確認 | 起動コマンド、IP・ポート・ログ先を確認する必要がある |
| 今日の実験用RED制御 | 提供された `radicon_udp_server_50cm.py` | `Kenshin/Kenshin/radicon_udp_server.py` に整理。50cm/XY機能を除去。実機稼働版との同一性は未確認 |
| RED側モーター依存 | `MotorControl.py` | `Kenshin/Kenshin/MotorControl.py` に必要クラスを同梱。元は旧GitHub版からのコピーで、実機版との照合は未完了 |
| 新しいPCコントローラー | Proコン / Xbox 360 | `Kenshin/CBox/` に送信コードと読み取り専用 `controller_check.py` を追加。ボタン割り当ては実機確認前 |
| Motive | Motive実験PC | 操作手順のみ。CSV書き出し設定の詳細は要確認 |

## UWB/アンカーの確認状況

ユーザー提供の研究室リポジトリ一覧では、`RED_UWB_control-software` の `add_Spresense_MultiIMU` ブランチに `MURATA_Type_2BP/Raspberrypi_Multisession/version04.06.00/` とSR150のsession/MultiSessionファイルが存在します。ただし、この接続から研究室のPrivateリポジトリは404となり、現行ソースのシリアル設定・アンカーID・起動引数・アンカー側サーバー・通信ポートは直接確認できていません。

過去の実験メモではUWB側FTDI FT230XとSpresense側CP2102Nが別々に認識されています。これは物理接続の過去記録であり、今日の接続保証ではありません。次回UWB使用時に `ls -l /dev/serial/by-id/` で再確認し、FTDI側を開くプロセス、使用するSR150コードの版、アンカー台数/ID、起動引数、アンカー側IP/ポート、CSV/CIR保存先を確定してください。UWBとSpresenseの同時動作も実機で未確認です。

## Raspberry Piの現行制御コードを安全に回収する

**Windows PowerShellで実行**。Raspberry Piではなく、Windowsのダウンロードフォルダへコピーするだけで、実機のファイルは変更しない：

```powershell
New-Item -ItemType Directory -Force "$HOME\Downloads\RED_Procon_Current" | Out-Null

scp red@192.168.1.247:/home/red/Red2.0-Control-Software/explore_algorithm/radicon_udp_server.py "$HOME\Downloads\RED_Procon_Current\"

scp red@192.168.1.247:/home/red/pospredict/record_csv.py "$HOME\Downloads\RED_Procon_Current\"
```

Pi側で追加の関連ファイルが必要か確認：

```bash
ls -l ~/Red2.0-Control-Software/explore_algorithm/{radicon_udp_server.py,Radicon.py,MotorControl.py,DS_TWR_SR150_Multisession2.py} 2>&1
```

`No such file` と出たファイルは場所を確認。**その場で移動・削除しない**。

Windows側の現行 `procon_send.py` は、PCにあるファイルそのものをバックアップしてから比較する。

回収後、制御コードのバージョンや依存関係を確認し、`Spresense_v2/for_raspberrypi/`・`Spresense_v2/for_pc/` のように**新規追加**する。ルートに置かれた旧版は残す。

## 動作・復元時の注意

- `Spresense_v2/tools/record_csv.py` は**GitHubで管理するコピー**。現在Piで動いている `~/pospredict/record_csv.py` を書き換えない。
- `Spresense_v2/` のファイルをPiへまるごと上書きすると、カスタマイズ済みのラジコン制御が消える可能性がある。実機版との差分確認を先に行う。
- UWBのFTDIとSpresenseのCP2102Nを取り違えない。USBの `ttyUSB0`、`ttyUSB1` は実験ごとに確認。
