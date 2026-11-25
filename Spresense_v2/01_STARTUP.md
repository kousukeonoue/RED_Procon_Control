# 01 — 実験の起動・記録・終了

**実機で動作確認した構成**を元にした手順。各プログラムは別のターミナルで起動し、実験中は画面を閉じない。

## 0. 事前確認

- Raspberry Pi（RED）の電源、Proコン接続、モーター周辺の安全を確認する。
- 実験時のPi IPは `192.168.1.247`（固定ではない。ネットワークが変われば確認）。
- Spresenseブリッジが既に動いていれば、**再起動せずそのまま使用**。
- タグ・アンカーのUSBシリアルとSpresenseのUSBシリアルを取り違えない。

Windows PowerShellからPiに接続（必要なSSH画面の数だけ開く）：

```powershell
ssh red@192.168.1.247
```

PiでUSB接続を確認：

```bash
ls -l /dev/serial/by-id/
```

2026-11-24に確認された例：

```text
usb-FTDI_FT230X_Basic_UART_DM86TTWC-if00-port0 -> ../../ttyUSB0   # UWB側
usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_36e558692611e911b0e745ad87f8ef3e-if00-port0 -> ../../ttyUSB1 # Spresense側
```

`ttyUSB0` / `ttyUSB1` は変わる可能性がある。**by-idを優先**。

## 1. SSH画面1：Spresenseデータ配信（TCP 5000）

```bash
cd ~/pospredict
python3 -B pospredict_bridge.py --port /dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_36e558692611e911b0e745ad87f8ef3e-if00-port0 --start --no-log
```

- 研究室の `pospredict_bridge.py` を使用。
- SpresenseとPiはUSBシリアル接続。ブリッジがTCP **5000** でデータを配信する。
- `--no-log` は自動ログ保存をしない設定。実験時のCSV記録とは別。
- 起動済みなら重複起動しない。Spresenseの物理RESETも不要。

## 2. SSH画面2：REDラジコンサーバー（UDP 5005）

```bash
cd ~/Red2.0-Control-Software/explore_algorithm
python3 -B radicon_udp_server.py --imu
```

- Windowsからの操作指令をUDP **5005** で受信。
- Spresense角度をTCP **127.0.0.1:5000** から受け取り、直進・旋回制御に使う。
- 実機の最新版には、直進補正と旋回の微調整がある（例：45°・5°）。**正確なボタン割り当てと最新版のコードは、現行ファイルを回収後に確定**。
- GitHubルートの旧 `for_raspberrypi/` とは違う可能性があるため、旧ファイルで上書きしない。

## 3. UWB/アンカー（追加のSSH画面）

研究室のUWB測距・データ保存プログラムを別画面で起動する。対象は **FTDI FT230X側** のシリアル。

以前の作業で登場したファイル：
- `~/Red2.0-Control-Software/explore_algorithm/DS_TWR_SR150_Multisession2.py`
- `UWB_Pile_Logger.py`、`UWB_RobotControl_Logger.py` 等（用途・保存先は現行ファイルの確認が必要）

**注意：UWBの最終的な起動引数（`r`, `timestamp`, `pair1first` 等）、アンカー側サーバーの実行場所・IP・ポートは未確認。** 正しい実機の起動履歴・コードを確認するまで、推測したコマンドで起動しない。

過去の実行コマンドを探すとき（実行するのではなく表示するだけ）：

```bash
history | grep -E 'DS_TWR|UWB_|anchor|Anchor|serial' | tail -30
```

アンカーの設置位置、ID、基準座標、タグ高さは実験ノートと一致させる。

## 4. Windows PowerShell：Proコン送信

```powershell
cd "$HOME\Desktop\for_pc\main"
python procon_send.py
```

- 実機PC側の `procon_send.py` がPiの現行IP（例：`192.168.1.247`）へ送信する設定か確認。
- 旧GitHub READMEに載るIP `192.168.1.171` は古い構成。
- REDが安全に停止できることを確認してから実験開始。

## 5. SSH画面3：Spresense CSV（実験時のみ）

Spresenseブリッジが動いている状態で起動：

```bash
python3 -B ~/pospredict/record_csv.py
```

`CSV記録開始:` と表示されれば成功。記録中にREDを操作できる。

**終了時だけ、このCSV画面で `Ctrl+C` を押す。** 記録件数と保存先が表示される。

保存先：`/home/red/pospredict/logs/spresense_YYYYMMDD_HHMMSS.csv`

このリポジトリの [tools/record_csv.py](tools/record_csv.py) は確認済みの記録コードのコピー。**Piですでに動いているものを急に置き換える必要はない**。

## 6. Motive

- REDとアンカーの剛体が正しく認識されているか確認。
- 実験中に録画し、終了後にCSV形式で書き出す。
- Spresenseの時刻はPi受信時刻なので、Motiveとの比較には時刻基準や同期ずれの確認が必要。

## 7. 終了順

1. REDを停止する。
2. Motiveの録画を停止・保存する。
3. Spresense CSV画面で `Ctrl+C`（**記録件数と保存ファイル**を確認）。
4. UWB計測を停止し、測距・CIRデータの保存を確認。
5. WindowsのProコン送信、Piのラジコンサーバーを停止する。
6. Spresenseブリッジは次も使うならそのままでよい。

## 8. WindowsにCSVをダウンロード

Windows PowerShell上で実行（Pi側のSSH画面ではない）：

```powershell
# 例：実験ファイル1つを取得
scp red@192.168.1.247:/home/red/pospredict/logs/spresense_20261124_154013.csv "$HOME\Downloads\"

# Spresense記録済みCSVをまとめて取得
scp "red@192.168.1.247:/home/red/pospredict/logs/spresense_*.csv" "$HOME\Downloads\"
```

UWBとMotiveのCSVは、それぞれの保存場所から別途回収する。

## 実験記録で最低限メモする情報

日時、走行内容（直進/後退/45°/90°旋回など）、アンカー台数と座標、各USBポート、各CSVのファイル名、Motive録画区間、時刻同期方法、使用した制御コードの版。
