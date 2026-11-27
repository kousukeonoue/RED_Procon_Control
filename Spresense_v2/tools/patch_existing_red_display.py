#!/usr/bin/env python3
"""Safely patch only console reporting of the existing RED control file."""
import ast
from datetime import datetime
from pathlib import Path
import shutil

p = Path.home() / "Red2.0-Control-Software" / "explore_algorithm" / "radicon_udp_server.py"
if not p.is_file():
    raise SystemExit(f"ERROR: ファイルがありません: {p}")
s = p.read_text(encoding="utf-8")
tag = "# RED_READABLE_LOG_INPLACE_V1"
if tag in s:
    raise SystemExit("ALREADY_PATCHED: 既に表示整理済み。変更しません")

old_calls = {
    'print("直進基準角度:", p)': '_red_log_start(p, command)',
    'print(f"IMU補正 P={p:.2f} 誤差={error:.2f} L={left} R={right}")':
        '_red_log_drive(p, error, left, right)',
    'print("recv:", cmd, "from", addr)': '_red_log_command(cmd)',
    'print("Spresense P =", imu_heading["p"], flush=True)':
        'pass  # 連続P表示を省略。角度取得・制御には影響なし',
}
required = [
    'def drive_with_imu(command, base=55):',
    'def turn_update():',
    'print("UDP server start : port 5005")',
]
for text in required + list(old_calls):
    if s.count(text) != 1:
        raise SystemExit(f"ERROR: この版のコードに適用できません: {text[:70]!r}\n変更なし")

helper = r'''
# RED_READABLE_LOG_INPLACE_V1
# These functions change ONLY the console output; motor control is untouched.
import time as _red_display_time

_red_run = None
_red_last_command = None


def _red_log_end(reason):
    global _red_run
    d = _red_run
    _red_run = None
    if not d or d["n"] == 0:
        return
    print(
        "\n========== 走行結果 ==========\n"
        f"方向: {d['mode']} / 終了: {reason}\n"
        f"基準P: {d['start']:+.2f}° / 最終P: {d['last_p']:+.2f}°\n"
        f"最終角度誤差: {d['last_e']:+.2f}°\n"
        f"平均絶対角度誤差: {d['sum']/d['n']:.2f}°\n"
        f"最大絶対角度誤差: {d['max']:.2f}°\n"
        f"時間: {_red_display_time.monotonic()-d['t']:.1f}秒 / {d['n']}回測定\n"
        "※Spresense P基準。横ずれ・距離は計測していません。\n"
        "==============================",
        flush=True,
    )


def _red_log_start(p_value, direction):
    global _red_run
    _red_log_end("次の走行")
    mode = "前進" if direction == "forward" else "後退"
    now = _red_display_time.monotonic()
    _red_run = {
        "mode": mode, "start": p_value, "last_p": p_value,
        "last_e": 0.0, "sum": 0.0, "max": 0.0,
        "n": 0, "t": now, "info": now,
    }
    print(f"\n[走行開始] {mode} / 基準P={p_value:+.2f}°", flush=True)


def _red_log_drive(p_value, error, left, right):
    d = _red_run
    if d is None:
        return
    d["last_p"], d["last_e"] = p_value, error
    d["sum"] += abs(error)
    d["max"] = max(d["max"], abs(error))
    d["n"] += 1
    now = _red_display_time.monotonic()
    if now - d["info"] >= 2.0:
        print(
            f"[走行中] P={p_value:+.2f}° / 誤差={error:+.2f}° / "
            f"最大={d['max']:.2f}° / L={left} R={right}",
            flush=True,
        )
        d["info"] = now


def _red_log_command(cmd):
    global _red_last_command
    if cmd in ("stop", "idle"):
        _red_log_end("停止")
    elif cmd in ("left", "right") or cmd.startswith("turn_"):
        _red_log_end("操作切替")
    kind = (
        "forward" if cmd in ("forward", "forward_fast") else
        "back" if cmd in ("back", "back_fast") else cmd
    )
    if cmd not in ("stop", "idle") and kind != _red_last_command:
        print(f"[操作] {cmd}", flush=True)
    _red_last_command = kind

'''
for before, after in old_calls.items():
    s = s.replace(before, after, 1)
s = s.replace(
    'print("UDP server start : port 5005")',
    helper + '\nprint("UDP server start : port 5005")',
    1,
)
# The original top-level finally still stops the robot. A normal Ctrl+C
# message replaces the traceback only if the expected structure is present.
if s.count("\nfinally:\n") == 1 and "\nexcept KeyboardInterrupt:\n" not in s:
    s = s.replace(
        "\nfinally:\n",
        '\nexcept KeyboardInterrupt:\n'
        '    _red_log_end("Ctrl+C")\n'
        '    print("Ctrl+C: REDを停止して終了します", flush=True)\n'
        'finally:\n',
        1,
    )
try:
    ast.parse(s, filename=str(p))
except SyntaxError as exc:
    raise SystemExit(f"ERROR: 構文確認に失敗したため変更なし: {exc}")
backup = p.with_name(
    "radicon_udp_server.before_readable_" +
    datetime.now().strftime("%Y%m%d_%H%M%S") + ".py"
)
shutil.copy2(p, backup)
tmp = p.with_name(p.name + ".readable_tmp")
tmp.write_text(s, encoding="utf-8")
tmp.replace(p)
print("RED_READABLE_LOG_INPLACE_V1 OK")
print("変更対象:", p)
print("バックアップ:", backup)
print("直進の計算・旋回の計算・PWM・安全停止には変更なし")
