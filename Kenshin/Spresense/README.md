# Spresense bridge

RED側の `radicon_udp_server.py` は TCP `127.0.0.1:5000` に接続し、Spresenseから届く `P:` の角度を使います。

現在確認できている実機上のブリッジ：
```text
/home/red/pospredict/pospredict_bridge.py
```

起動例（ポート名は毎回 `ls -l /dev/serial/by-id/` で確認し、実機のCP2102N名に置き換える）：
```bash
cd ~/pospredict
python3 -B pospredict_bridge.py --port /dev/serial/by-id/<SpresenseのCP2102Nデバイス名> --start --no-log
```

**このGitHubフォルダには `pospredict_bridge.py` 本体はまだ収録していません。** Pi上の実ファイル本文を取得できていないため、別コードで代用・再作成していません。完全に自己完結させるには、実機の `~/pospredict/pospredict_bridge.py` をこのフォルダへコピーする必要があります。

CSV記録は既存の `Spresense_v2/tools/record_csv.py` が別途あります。通常操作では自動CSV記録を行わない運用です。
