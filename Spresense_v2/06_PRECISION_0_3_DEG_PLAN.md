# 06 — Proコンでの旋回誤差0.3°未満・直進精度向上のためのコード監査と実験計画

調査：2026-11-27。**研究室の実機は未操作**。GitHubのコードと公開ドキュメントを照合した設計・検証メモ。既存ファイルは変更していない。

## 目標の区別

1. **Spresense P基準**：コマンド目標角から停止後P差分の誤差が絶対値0.3°未満。
2. **Motive実際角度基準**：剛体yaw差分が目標角に対して絶対値0.3°未満。
3. 成功率：各方向・角度を繰り返して **0.3°未満を満たした割合**も評価。表示分解能0.01°と測定精度は別。
4. 直進・後退は **角度誤差のほか横ずれ[cm]・平均偏差・最大偏差**をMotiveで評価。

## 確認したGitHubソース（2026-11-27取得）

- `Spresense_v2/Kenshin/Kenshin/radicon_udp_server.py`
- `Spresense_v2/Kenshin/Kenshin/MotorControl.py`
- `Spresense_v2/Kenshin/CBox/procon_send_kenshin.py`
- `Spresense_v2/Kenshin/CBox/controller_check.py`
- `Kenshin/RED/radicon_udp_server.py`
- `for_raspberrypi/radicon_udp_server.py`

比較：`Kenshin/RED/radicon_udp_server.py` と `Spresense_v2/Kenshin/Kenshin/radicon_udp_server.py` は確認時、GitHub blob SHAが同じでコード本体は同一。**しかし実機の `~/Red2.0-Control-Software/explore_algorithm/radicon_udp_server.py` と同一かは未確認**。

## 実際の主要パラメータ（GitHubのKenshin版）

| パラメータ | 現在GitHubコードの値 |
|---|---|
| 通信 | UDP 5005、Spresense TCP 127.0.0.1:5000 |
| 制御待機ループ | `time.sleep(0.005)`（5msの待機、実周期は処理負荷により変動） |
| 直進通常/高速PWM | 48 / 65 |
| 前進PID Kp/Ki/Kd | 0.9 / 0.35 / 0.05 |
| 後退PID Kp/Ki/Kd | 1.2 / 0.55 / 0.05 |
| 後退フィードフォワード補正 | -3.0 |
| 最大左右PWM補正量 | 12 |
| PWMの整数化 | `int(...)` |
| 直進基準リセット | `mode != cmd` で基準を再取得（高速/通常切替でもリセット） |
| 旋回 | 5°/45°/90°、方向左右 |
| 旋回の先読み | 角速度 × 0.08秒、5°は1.5–3.5°、それ以外は2–7°に制限 |
| 旋回後 | ブレーキ0.15秒、合計約0.55秒経過後の角度を確認 |
| 合格閾値 | ±0.5°（**0.3°ではない**） |
| 微修正 | PWM45、パルス長18–55ms、最大5回 |
| IMU/UDP更新許容 | IMU 0.6秒、UDP 0.4秒 |

## 調査上の重要な懸念点

### 1. pigpioのPWM実周波数／分解能（最優先で読み取り確認）

`MotorControl.py` は `__FREQ=50000`、`__RANGE=100`、GPIO 27/22/19/26に `set_PWM_frequency`。
pigpioの **通常ソフトウェアPWM** では要求周波数と実現周波数が異なる。標準のpigpiodサンプル周期5µsでは最大8kHzであり、50kHzを指定しても50kHzのPWMにはならない。
モータードライバBD6231Fのメーカー仕様はPWM入力周波数20–100kHz。実機で **`get_PWM_frequency` と `get_PWM_real_range`** を最初に確認する。制御分解能が低い可能性もある。
GPIO変更やPWM方式切替（ハードウェアPWM、別のモータ制御器など）は配線と既存設定を調査してから。**実機を確認する前に `__FREQ` だけ勝手に変えない**。

読み取り確認コマンド（Pi・ラジコン停止状態でpigpiodが生きているときに実行。コードの設定は変更しない）：

```bash
python3 - <<'PY'
import pigpio
pi = pigpio.pi()
assert pi.connected, "pigpiod not connected"
for pin in (27, 22, 19, 26):
    print(pin, "Hz:", pi.get_PWM_frequency(pin),
          "range:", pi.get_PWM_range(pin),
          "real_range:", pi.get_PWM_real_range(pin))
pi.stop()
PY
```

**起動前に読むとPWM周波数は初期値である可能性がある**。実機でこのコマンドを実行する際は、現在稼働中のサーバーや停止状態を確認してから読み取る。

### 2. 最小微修正量（0.3°狙いの物理限界）
- 現行コード最短 **18ms × PWM45**。これでREDが実際に何度回るかを左右各10回、停止後0.5秒/1秒で測定。
- 最小ステップが0.3°以上、またはばらつきが0.3°以上なら、`abs(error) <= 0.3` にするだけでは達成不可能。より精細なPWM、減速プロファイル、滑り低減、短いモータ駆動のタイミング精度が必要。
- 微修正回数を増やすだけでは発振や行き過ぎの危険。安全な停止条件を維持。

### 3. 速度変更時の基準角リセット（直進に不利）
`if mode != cmd:` で `target=angle`。たとえば `forward` → `forward_fast` で方向が同じでも目標角を取り直す。
**改善案**：前進/後退方向が同じなら目標角を維持し、手動で停止・方向転換後の新しい走行でのみ新しい基準角を決める。実機コードの指令を見て実装する。

### 4. PC Proコン送信側とPi受信側の不一致
PiのKenshinコードは `forward_fast` と `back_fast` を受け付けるが、GitHubの `procon_send_kenshin.py` は通常 `forward` / `back` を送る構造で高速コマンド送信がない。ボタン対応・左右軸・トリガーも `controller_check.py` の結果と照合。
**改善案**：Proコンの各ボタンとスティック実値を確認し、通信コマンドの表を作り統一する。

### 5. 誤差の定義とログ不足
- GitHubのKenshin版は `STRAIGHT RESULT` を標準出力に記録し、旋回結果も文字ログ。これだけでは各時点の実PWM、目標角、角速度、ブレーキ開始、モーター応答を解析しづらい。
- **実験時だけ**スクリプトの `--log` 等で1本の操作ログCSVに `time_ns,monotonic_ns,mode,target_angle,P,angular_rate,error,pwm_L,pwm_R,turn_phase,trim_pulse,command` を記録する設計が必要。
- `record_csv.py` の SpresenseログはTCP受信時刻で、真のセンササンプリング時刻ではない。Motive比較の遅延とオフセットは計測して合わせる。

### 6. 物理精度の壁
- IMU `P` の符号・軸・ゲインをMotive yaw差分と左右旋回で照合。静止30〜60秒のノイズ・ドリフト、停止後1〜2秒の変化を見る。
- Motive剛体のマーカ配置（できるだけ広げる）、遮蔽、キャリブレーション品質を確認。角度0.3°は、半径10cmのマーカ位置で約0.52mmの横方向移動量に相当。
- 角度の読み取り分解能（小数点以下2桁）と実角度の正確さは異なる。

## 次回実験のおすすめ順

**A（初日最初）：現在動いているPiコードの読み取りコピー・SHA256**
`radicon_udp_server.py`、使用 `MotorControl.py`、PC `procon_send.py`、ブリッジなど。Kenshin版の上書きはしない。公開許可を確認し、確認済みソースだけGitHubに分離保存。

**B：PWM周波数・実分解能確認**（上記読み取りスクリプト）。次に安全な条件で、左右の微小回転パルスの最小角度とばらつきをMotiveで測る。

**C：Motive基準の評価**
- REDを静止させ30〜60秒間のP値とMotive yawを記録。
- 5°/45°/90°、左右それぞれまず3回→余裕があれば10回ずつ。最終時刻は停止後0.5秒・1秒・2秒で確認。
- エラーは `wrap(yaw_Motive(end)-yaw_Motive(start))-target` と、同様の `P` 差分誤差を**分けて出す**。
- 成功割合 `abs(error)<0.3°`、平均絶対誤差、中央値、95パーセンタイル、最大値、回転の横滑り（Motive x,y）も集計。

**D：直進・後退の評価**
- 同じ床・電池・速度で、50cm/1mの前進/後退（スティック手動操作）を左右偏差・平均角度偏差で比較。
- 上述の `mode` 変更時の基準角リセット修正、モーター左右の固定偏差・後退特有のバイアス、PIDゲイン調整を**一つずつ**実施。
- 方位保持だけでは開始時の横ずれが残る。後でMotive/UWB位置フィードバックを追加する。

**E：旋回改善**
- 最小微修正量が0.3°より小さく、Motive yawにも追随するなら、合格閾値を **0.5°→0.3°** とした実験ブランチで改良（微修正回数を単純増加させない）。
- 停止先読み係数・低速PWM・ブレーキ長を実測で校正。速度・加速度制約を持つ旋回プロファイルと、角度＋角速度のPD制御も比較。
- 実装では安全停止・IMU通信タイムアウト・UDP監視を維持する。

## 公開資料

- pigpio `set_PWM_frequency`, `get_PWM_real_range`: https://github.com/joan2937/pigpio/blob/master/pigpio.py
- ROHM BD6231F（PWM入力周波数20〜100kHz）: https://www.rohm.co.jp/products/motor-actuator-drivers/dc-brush-motor/bd6231f-product
- OptiTrack Rigid Body Tracking（マーカ配置と姿勢推定）: https://docs.optitrack.com/motive/rigid-body-tracking
- OptiTrack calibration: https://docs.optitrack.com/motive/calibration
- WPILib Profiled PID Controller（台形速度プロファイル、制御）: https://docs.wpilib.org/en/latest/docs/software/advanced-controls/controllers/profiled-pidcontroller.html
- WPILib feedforward（制御系のモデル・フィードフォワード）: https://docs.wpilib.org/en/latest/docs/software/advanced-controls/controllers/feedforward.html

## 未確認事項

実機の現行PiサーバーがこのGitHub版と完全一致するか、Spresenseの `P` と真のロボットyawの一致度、pigpioの実PWM周波数、制御対象の最小旋回角、Motiveキャリブレーションの状態、センサ同期遅延、車輪エンコーダ有無。**測定前に0.3°達成できたとは主張しない**。
