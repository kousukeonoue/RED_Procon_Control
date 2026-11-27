#!/usr/bin/env python3
"""Run the current RED server with concise console output; no motor code edits."""
import builtins
import re
import runpy
import sys
import time
from pathlib import Path

original_print = builtins.print
server = Path(__file__).with_name("radicon_udp_server.py")
state = {"cmd": "", "straight": None, "turn": None}
def show(s):
    original_print(s, flush=True)
def grab(label, s):
    match = re.search(label + r"=([+-]?\d+(?:\.\d+)?)", s)
    return float(match.group(1)) if match else None
def end_drive(reason):
    d = state["straight"]
    state["straight"] = None
    if not d: return
    n = d["n"]
    if n:
        show("\n==== 直進・後退結果 (" + reason + ") ====\n"
             + f"方向={d['mode']}  基準P={d['start']:+.2f}°  最終P={d['last_p']:+.2f}°\n"
             + f"最終誤差={d['last_e']:+.2f}°  平均絶対誤差={d['sum']/n:.2f}°  最大誤差={d['peak']:.2f}°\n"
             + f"時間={time.monotonic()-d['t']:.1f}秒 / {n}サンプル\n"
             + "※Spresense角度基準。位置・距離の誤差ではありません\n==========================\n")
def end_turn(reason):
    t = state["turn"]
    state["turn"] = None
    if not t or t["error"] is None: return
    e = t["error"]
    show("\n==== 旋回結果 (" + reason + ") ====\n"
         + f"指定={t['target']:+.2f}°  実際={t['actual']:+.2f}°\n"
         + f"最終誤差={e:+.2f}° (絶対値{abs(e):.2f}°) / 微修正{t['n']}回\n"
         + ("0.3°未満：達成" if abs(e) < 0.3 else "0.3°未満：未達")
         + "\n※Spresense P角度基準\n======================\n")
def filtered(*args, **kw):
    s = " ".join(map(str, args))
    now = time.monotonic()
    if s.startswith("recv:"):
        parts = s.split()
        if len(parts) > 1:
            cmd = parts[1]
            if cmd in ("stop", "idle", "left", "right") or cmd.startswith("turn_"):
                end_drive("停止" if cmd in ("stop", "idle") else "切替")
            state["cmd"] = cmd
        return
    if s.startswith("Spresense P ="): return
    if s.startswith("直進基準角度:"):
        end_drive("切替")
        match = re.search(r"角度:\s*([+-]?\d+(?:\.\d+)?)", s)
        if match:
            p = float(match.group(1))
            mode = "後退" if state["cmd"].startswith("back") else "前進"
            state["straight"] = {"mode": mode, "start": p, "last_p": p, "last_e": 0.,
                                  "n": 0, "sum": 0., "peak": 0., "t": now, "status": now}
            show(f"\n[走行開始] {mode} / 基準P={p:+.2f}°")
            return
    if s.startswith("IMU補正 P="):
        m = re.search(r"P=([+-]?[\d.]+)\s+誤差=([+-]?[\d.]+)\s+L=(\d+)\s+R=(\d+)", s)
        d = state["straight"]
        if m and d:
            p, e = float(m.group(1)), float(m.group(2))
            d["last_p"], d["last_e"] = p, e
            d["n"] += 1
            d["sum"] += abs(e)
            d["peak"] = max(d["peak"], abs(e))
            if now - d["status"] > 2:
                show(f"[走行中] P={p:+.2f}° 誤差={e:+.2f}° 最大={d['peak']:.2f}° L={m.group(3)} R={m.group(4)}")
                d["status"] = now
            return
    if "角度ずれ20度超過" in s or "IMU未取得・通信異常" in s:
        end_drive("異常停止")
        show("[警告] " + s)
        return
    if s.startswith("旋回開始"):
        end_drive("旋回開始")
        end_turn("次の旋回")
        t = grab("指定", s)
        if t is not None:
            state["turn"] = {"target": t, "actual": None, "error": None, "n": 0}
            show(f"\n[旋回開始] {'左' if t > 0 else '右'}{abs(t):g}°")
            return
    if s.startswith("旋回ブレーキ直後"):
        e = grab("誤差", s)
        if e is not None:
            show(f"[ブレーキ直後] 誤差={e:+.2f}°")
            return
    if s.startswith("停止後角度") or s.startswith("微調整後"):
        t = state["turn"]
        a, e = grab("実際", s), grab("誤差", s)
        if t and a is not None and e is not None:
            t["actual"], t["error"] = a, e
            show(f"[{'微修正後' if s.startswith('微調整後') else '停止後'}] 実際={a:+.2f}° 誤差={e:+.2f}°")
            if s.startswith("停止後角度") and abs(e) <= 1.0:
                # Current Pi code does not trim <=1 degree.
                end_turn("停止後")
            return
    if s.startswith("微調整") and "開始" in s:
        t = state["turn"]
        if t: t["n"] += 1
        show("[微修正] " + s)
        return
    if s.startswith("微調整終了"):
        end_turn("微修正後")
        return
    original_print(*args, **kw)
def main():
    if not server.is_file():
        raise SystemExit("元のラジコンコードが見つかりません: " + str(server))
    show("[表示整理モード] 元の制御プログラムは変更しません")
    old_arg0 = sys.argv[0]
    builtins.print = filtered
    sys.argv[0] = str(server)
    try:
        runpy.run_path(str(server), run_name="__main__")
    except KeyboardInterrupt:
        pass
    finally:
        builtins.print = original_print
        sys.argv[0] = old_arg0
        end_drive("終了")
        end_turn("終了")
        show("[表示整理モード終了]")
if __name__ == "__main__":
    main()
