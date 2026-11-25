#!/usr/bin/env python3
"""Spresense bridge TCP 5000 output -> experimental CSV on Raspberry Pi.

Start after pospredict_bridge.py with --no-log; stop only this recorder with Ctrl+C.
Known output in 2026-11-24 experiments: 1,212 and 17,064 data rows.
"""
import socket
import csv
import re
import time
from datetime import datetime
from pathlib import Path

folder = Path.home() / "pospredict" / "logs"
folder.mkdir(parents=True, exist_ok=True)
path = folder / ("spresense_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv")

# Incoming text example: X:0.00 Y:0.00 Z:0.00 R:-0.39 Y:-1.97 P:-101.11
# The second Y is the angular field; P is used in the current RED turn controller.
pattern = re.compile(
    r"X:\s*([-+]?\d+(?:\.\d+)?)\s+"
    r"Y:\s*([-+]?\d+(?:\.\d+)?)\s+"
    r"Z:\s*([-+]?\d+(?:\.\d+)?)\s+"
    r"R:\s*([-+]?\d+(?:\.\d+)?)\s+"
    r"Y:\s*([-+]?\d+(?:\.\d+)?)\s+"
    r"P:\s*([-+]?\d+(?:\.\d+)?)"
)

count = 0
try:
    with socket.create_connection(("127.0.0.1", 5000), 5) as sock:
        with sock.makefile("r", encoding="utf-8", errors="replace") as stream:
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                # Keep the original tested column names; 'pitch' is incoming P.
                writer.writerow(["time", "unix_ns", "x", "y", "z", "roll", "yaw", "pitch"])
                print("CSV記録開始:", path, flush=True)
                print("終了は Ctrl+C", flush=True)
                for line in stream:
                    match = pattern.search(line)
                    if not match:
                        continue
                    ns = time.time_ns()
                    timestamp = datetime.fromtimestamp(ns / 1e9).astimezone().isoformat(timespec="milliseconds")
                    writer.writerow([timestamp, ns, *match.groups()])
                    count += 1
                    if count % 100 == 0:
                        f.flush()
except KeyboardInterrupt:
    print("\nCSV記録終了")
except OSError as e:
    print("通信エラー:", e)
print("保存先:", path)
print("記録件数:", count)
