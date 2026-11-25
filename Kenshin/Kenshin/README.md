# Nintendo Switch Pro Controller

実行ファイル：`procon_send_kenshin.py`

- B / A：前進 / 後退
- 左スティック：連続移動・左右旋回
- X / Y：停止
- 十字キー上 / 下：前進 / 後退
- 十字キー左 / 右：5°旋回
- L / R：45°旋回
- 左 / 右トリガー：90°旋回
- 右スティック：未使用（50 cm走行機能を削除したため）

起動：
```powershell
python -m pip install pygame
python .\procon_send_kenshin.py
```

スクリプト先頭の `RED_IP` をREDの現在のIPに合わせてください。
