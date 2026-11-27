#!/usr/bin/env python3
"""Guarded in-place precision test patch for the existing RED server.
Stops without changing files when the live source differs. Use --apply to write.
"""
import argparse
import ast
from datetime import datetime
from pathlib import Path
import shutil

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
args = ap.parse_args()
p = Path.home() / "Red2.0-Control-Software/explore_algorithm/radicon_udp_server.py"
if not p.is_file():
    raise SystemExit("ERROR: source file missing: " + str(p))
s = p.read_text(encoding="utf-8")
if "# RED_PRECISION_TURN_STAGE1_V1" in s:
    raise SystemExit("ALREADY PATCHED: no changes.")
if "# RED_READABLE_LOG_INPLACE_V1" not in s:
    raise SystemExit("ERROR: readable-console version not found; no changes.")

changes = [
    (
      "pass  # 連続P表示を省略。角度取得・制御には影響なし",
      'if not globals().get("_red_initial_p_shown", False):\n'
      '                                print(f"Spresense 初期P = {imu_heading[\'p\']:+.2f}°", flush=True)\n'
      '                                globals()["_red_initial_p_shown"] = True',
      "初期Pを一度表示"
    ),
    (
      "lead_min = 2.0 if requested >= 30 else 0.8",
      "lead_min = 1.3 if requested >= 30 else 0.8  # RED_PRECISION_TURN_STAGE1_V1",
      "45/90°の最小停止先読みを2.0°から1.3°で試験"
    ),
    ("if 1.0 < abs(err) <= 4.0:", "if 0.3 < abs(err) <= 4.0:", "微修正の開始閾値"),
    ("abs(err) <= 1.0", "abs(err) < 0.3", "微修正の完了閾値"),
    ('state["attempt"] >= 2', 'state["attempt"] >= 4', "微修正上限4回"),
]
for old, new, name in changes:
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"ERROR: expected 1 match for {name}, got {n}; no changes.")
for line in s.splitlines():
    if changes[0][0] in line:
        indent = len(line) - len(line.lstrip())
        if indent != 28:
            raise SystemExit(f"ERROR: unexpected P indent {indent}; no changes.")
updated = s
for old, new, _ in changes:
    updated = updated.replace(old, new, 1)
try:
    ast.parse(updated, filename=str(p))
except SyntaxError as e:
    raise SystemExit(f"ERROR: Syntax failed; no changes: {e}")
print("CHECK OK: version and Python syntax.")
for _, _, name in changes:
    print(" -", name)
print("Motor, GPIO, UDP, IMU disconnect and emergency-stop code unchanged.")
if not args.apply:
    print("DRY RUN: python3 -B /tmp/patch_red_precision_stage1.py --apply")
    raise SystemExit(0)
backup = p.with_name("radicon_udp_server.before_precision_" +
                     datetime.now().strftime("%Y%m%d_%H%M%S") + ".py")
shutil.copy2(p, backup)
tmp = p.with_name(p.name + ".precision_tmp")
try:
    tmp.write_text(updated, encoding="utf-8")
    ast.parse(tmp.read_text(encoding="utf-8"))
    tmp.replace(p)
finally:
    tmp.unlink(missing_ok=True)
print("APPLIED: existing server modified.")
print("BACKUP:", backup)
print("Next: test one +45° and one -45° at low risk; tune further from results.")
