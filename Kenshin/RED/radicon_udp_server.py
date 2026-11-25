import socket
import threading
import time
import re
import math
import pigpio
import MotorControl

UDP_PORT = 5005
IMU_PORT = 5000

BASE_PWM = 48
HIGH_PWM = 65
KP = 0.9
KI = 0.35
KD = 0.05

KP_BACK = 1.2
KI_BACK = 0.55
KD_BACK = 0.05
MAX_CORRECTION = 12
IMU_TIMEOUT = 0.6
UDP_TIMEOUT = 0.4
MAX_HEADING_ERROR = 25

yaw = None
yaw_time = 0
yaw_rate = 0
imu_lock = threading.Lock()

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def wrap(x):
    return (x + 180) % 360 - 180

def imu_reader():
    global yaw, yaw_time, yaw_rate

    while True:
        try:
            with socket.create_connection(
                ("127.0.0.1", IMU_PORT), timeout=2
            ) as s:
                s.settimeout(0.6)

                with s.makefile("r") as f:
                    for line in f:
                        m = re.search(
                            r"\bP:\s*([-+]?\d+(?:\.\d+)?)",
                            line
                        )
                        if not m:
                            continue

                        value = float(m.group(1))
                        if not math.isfinite(value):
                            continue

                        now = time.monotonic()

                        with imu_lock:
                            dt = now - yaw_time

                            if yaw is not None and 0.005 < dt < 0.2:
                                rate = wrap(value - yaw) / dt
                                yaw_rate = 0.85 * yaw_rate + 0.15 * rate
                            else:
                                yaw_rate = 0

                            yaw = value

                            yaw_time = now

        except (OSError, ValueError):
            pass

        finally:
            with imu_lock:
                yaw = None
                yaw_time = 0
                yaw_rate = 0

        time.sleep(0.3)

def get_imu():
    with imu_lock:
        return yaw, yaw_time, yaw_rate

class Drive:
    def __init__(self, gpio):
        self.left = MotorControl.BD6231(gpio, 27, 22)
        self.right = MotorControl.BD6231(gpio, 19, 26)
        self.stop()

    def motor(self, motor, pwm, reversed_motor):
        pwm = int(clamp(pwm, -100, 100))

        if pwm == 0:
            motor.stop_rotation()
            return

        forward = pwm > 0

        if reversed_motor:
            forward = not forward

        if forward:
            motor.forward_rotation_pwm(abs(pwm))
        else:
            motor.backward_rotation_pwm(abs(pwm))

    def move(self, left, right):
        self.motor(self.left, -left, True)
        self.motor(self.right, -right, False)

    def brake(self):
        self.left.break_rotation()
        self.right.break_rotation()

    def stop(self):
        self.left.stop_rotation()
        self.right.stop_rotation()

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", UDP_PORT))
    sock.setblocking(False)

    gpio = pigpio.pi()

    if not gpio.connected:
        sock.close()
        raise RuntimeError("pigpiod connection failed")

    drive = Drive(gpio)

    threading.Thread(
        target=imu_reader,
        daemon=True
    ).start()

    mode = "stop"
    target = None
    last_packet = 0
    turn_start = 0
    turn_angle = 0
    turn_direction = 0
    turn_deadline = 0
    settle_until = 0
    last_cmd = ""
    brake_until = 0
    correction_count = 0
    previous_error = float("inf")
    pulse_until = 0
    pulse_gain = 40.0
    previous_signed_error = None
    last_pulse = 0.0
    last_status = 0
    blocked = False
    errors = []
    drive_started = 0
    integral = 0.0
    pid_time = time.monotonic()
    desired_heading = None

    def finish_straight(reason):
        if errors:
            mae = sum(abs(e) for e in errors) / len(errors)
            peak = max(abs(e) for e in errors)
            print(
                f"STRAIGHT RESULT [{reason}] "
                f"MeanAbsError={mae:.2f}deg "
                f"MaxError={peak:.2f}deg "
                f"FinalError={errors[-1]:.2f}deg "
                f"Time={time.monotonic()-drive_started:.2f}s",
                flush=True
            )
            errors.clear()

    print("UDP server ready: 5005", flush=True)

    try:
        while True:
            now = time.monotonic()
            angle, stamp, rate = get_imu()

            imu_ok = (
                angle is not None
                and now - stamp < IMU_TIMEOUT
            )

            while True:
                try:
                    data, addr = sock.recvfrom(1024)
                except BlockingIOError:
                    break

                cmd = data.decode(errors="ignore").strip()

                valid = (
                    cmd in ("stop", "keepalive", "forward",
                            "back", "forward_fast", "back_fast",
                            "left", "right")
                    or cmd in (
                        "left5", "right5",
                        "left45", "right45",
                        "left90", "right90"
                    )
                )

                if not valid:
                    continue

                last_packet = time.monotonic()

                if cmd == "keepalive":
                    last_cmd = cmd
                    continue

                if cmd == "stop":
                    finish_straight("released")
                    blocked = False
                    mode = "stop"
                    target = None
                    brake_until = 0
                    drive.stop()

                elif imu_ok and not blocked:
                    if cmd in (
                        "forward", "back",
                        "forward_fast", "back_fast"
                    ):
                        if mode != cmd:
                            drive.stop()
                            finish_straight("mode change")
                            target = angle
                            errors.clear()
                            drive_started = now
                            integral = 0.0
                            pid_time = now
                            desired_heading = None
                            mode = cmd

                    elif cmd in ("left", "right"):
                        if mode != cmd:
                            drive.stop()
                            mode = cmd
                            target = None

                    elif cmd != last_cmd:
                        drive.stop()
                        turn_angle = int(
                            re.search(r"\d+", cmd).group()
                        )
                        turn_direction = (
                            1 if cmd.startswith("left") else -1
                        )
                        turn_start = angle
                        correction_count = 0
                        pulse_gain = 40.0
                        previous_signed_error = None
                        last_pulse = 0.0
                        previous_error = float("inf")
                        turn_deadline = now + 5
                        mode = "turn"

                        print(
                            "TURN:", cmd,
                            "start:", angle,
                            flush=True
                        )

                last_cmd = cmd

            now = time.monotonic()
            angle, stamp, rate = get_imu()
            imu_ok = angle is not None and now-stamp < IMU_TIMEOUT

            if (
                not imu_ok
                or now - last_packet > UDP_TIMEOUT
            ):
                if mode != "stop":
                    finish_straight("signal lost")
                    blocked = True
                drive.stop()
                mode = "stop"
                target = None

            elif mode in (
                "forward", "back",
                "forward_fast", "back_fast"
            ):
                error = wrap(target - angle)

                errors.append(error)

                if abs(error) > MAX_HEADING_ERROR:
                    finish_straight("heading limit")
                    blocked = True
                    drive.stop()
                    mode = "stop"
                    target = None
                else:
                    dt = clamp(now - pid_time, 0.0, 0.05)
                    pid_time = now

                    backward = mode.startswith("back")

                    kp = KP_BACK if backward else KP
                    ki = KI_BACK if backward else KI
                    kd = KD_BACK if backward else KD

                    next_integral = clamp(
                        integral + error * dt,
                        -12.0, 12.0
                    )

                    raw = (
                        (-3.0 if backward else 0.0)
                        + kp * error
                        + ki * next_integral
                        - kd * rate
                    )

                    if abs(raw) <= MAX_CORRECTION:
                        integral = next_integral

                    correction = clamp(
                        (-3.0 if backward else 0.0)
                        + kp * error
                        + ki * integral
                        - kd * rate,
                        -MAX_CORRECTION,
                        MAX_CORRECTION
                    )

                    base = (
                        HIGH_PWM if mode.endswith("fast")
                        else BASE_PWM
                    )
                    direction = (
                        1 if mode.startswith("forward") else -1
                    )

                    left_pwm = -direction * base - correction
                    right_pwm = -direction * base + correction

                    drive.move(left_pwm, right_pwm)

                    if now - last_status >= 0.25:
                        print(
                            f"STRAIGHT Target={target:.2f} "
                            f"Yaw={angle:.2f} "
                            f"Error={error:.2f} "
                            f"Rate={rate:.2f} Corr={correction:.2f} "
                            f"L={left_pwm:.1f} "
                            f"R={right_pwm:.1f}",
                            flush=True
                        )
                        last_status = now

            elif mode == "left":
                drive.move(-45, 45)

            elif mode == "right":
                drive.move(45, -45)

            elif mode == "turn":
                progress = (
                    wrap(angle - turn_start)
                    * turn_direction
                )

                remaining = turn_angle - progress

                if turn_angle == 5:
                    pwm = 48
                    lead = clamp(
                        rate * turn_direction * 0.08,
                        1.5, 3.5
                    )
                else:
                    pwm = (
                        51 if remaining > 18
                        else 48 if remaining > 8
                        else 45
                    )

                    lead = clamp(
                        rate * turn_direction * 0.08,
                        2, 7
                    )

                if remaining <= lead:
                    drive.brake()
                    brake_until = now + 0.15
                    settle_until = now + 0.55
                    mode = "settle"

                elif now > turn_deadline or progress < -8:
                    drive.stop()
                    mode = "stop"
                    print(f"TURN aborted: Target={turn_angle:.2f} Actual={progress:.2f} Error={turn_angle-progress:.2f}", flush=True)

                else:
                    drive.move(
                        -turn_direction * pwm,
                        turn_direction * pwm
                    )

            elif mode == "micro":
                if now >= pulse_until:
                    drive.brake()
                    brake_until = now + 0.15
                    settle_until = now + 0.55
                    mode = "settle"

            elif mode == "settle":
                if now >= brake_until:
                    drive.stop()

                if now >= settle_until:
                    actual = wrap(angle - turn_start) * turn_direction
                    error = turn_angle - actual

                    print(
                        f"Target={turn_angle:.2f} "
                        f"Actual={actual:.2f} "
                        f"Error={error:.2f} "
                        f"Correction={correction_count}",
                        flush=True
                    )

                    if abs(rate) > 8:
                        drive.stop()
                        mode = "stop"
                        print("STOP: unstable angle", flush=True)

                    elif abs(error) <= 0.5:
                        drive.stop()
                        mode = "stop"
                        print("CONVERGED", flush=True)
                        print("===== TURN RESULT =====", flush=True)
                        print(f"Target angle : {turn_angle:.2f} deg", flush=True)
                        print(f"Actual angle : {actual:.2f} deg", flush=True)
                        print(f"Final error  : {abs(error):.2f} deg", flush=True)
                        print(f"Corrections  : {correction_count}", flush=True)
                        print("Tolerance    : 0.50 deg", flush=True)
                        print("Result       : " + ("PASS" if abs(error) <= 0.5 else "FAIL"), flush=True)
                        print("=======================", flush=True)

                    elif (
                        correction_count >= 5
                        or abs(error) > 4
                        or abs(error) > previous_error + 0.10
                    ):
                        drive.stop()
                        mode = "stop"
                        print("STOP: correction limit", flush=True)
                        print("===== TURN RESULT =====", flush=True)
                        print(f"Target angle : {turn_angle:.2f} deg", flush=True)
                        print(f"Actual angle : {actual:.2f} deg", flush=True)
                        print(f"Final error  : {abs(error):.2f} deg", flush=True)
                        print(f"Corrections  : {correction_count}", flush=True)
                        print("Tolerance    : 0.50 deg", flush=True)
                        print("Result       : " + ("PASS" if abs(error) <= 0.5 else "FAIL"), flush=True)
                        print("=======================", flush=True)

                    else:
                        previous_error = abs(error)
                        correction_count += 1

                        d = turn_direction * (
                            1 if error > 0 else -1
                        )

                        if previous_signed_error is not None and last_pulse > 0:
                            improvement = (
                                previous_signed_error - error
                            ) * (
                                1 if previous_signed_error > 0 else -1
                            )

                            if improvement > 0.10:
                                measured_gain = improvement / last_pulse
                                pulse_gain = clamp(
                                    0.5 * pulse_gain + 0.5 * measured_gain,
                                    15.0, 100.0
                                )
                            else:
                                pulse_gain = max(15.0, pulse_gain * 0.65)

                        pulse = clamp(
                            0.8 * abs(error) / pulse_gain,
                            0.018,
                            0.055
                        )

                        previous_signed_error = error
                        last_pulse = pulse
                        if abs(error) < 0.8:
                            pulse = min(pulse, 0.018)
                            last_pulse = pulse

                        print(
                            f"MICRO {correction_count}/5 "
                            f"Error={error:.2f} "
                            f"Pulse={pulse*1000:.0f}ms",
                            flush=True
                        )

                        drive.move(-d * 45, d * 45)
                        pulse_until = now + pulse
                        mode = "micro"

            else:
                drive.stop()

            time.sleep(0.005)

    except KeyboardInterrupt:
        pass

    finally:
        drive.stop()
        gpio.stop()
        sock.close()

if __name__ == "__main__":
    main()