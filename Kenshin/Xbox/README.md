# Xbox 360 Controller

実行ファイル：`xbox_send_kenshin.py`

今回のpygame認識に基づく割り当て：
- Y / A：前進 / 後退
- 左スティック：連続移動・左右旋回
- Back：停止
- X / B：左 / 右5°旋回
- LB / RB：左 / 右45°旋回
- LT / RT：左 / 右90°旋回
- 十字キー上 / 下：前進 / 後退
- 十字キー左 / 右：左 / 右5°旋回

起動：
```powershell
python -m pip install pygame
python .\xbox_send_kenshin.py
```

スクリプト先頭の `RED_IP` をREDの現在のIPに合わせてください。
