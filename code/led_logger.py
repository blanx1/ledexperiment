"""
Live I-V logger for the Planck's constant LED experiment.

Reads the CSV lines printed by planck_led_logger.ino, plots LED current vs
voltage live, and saves every point to <led_name>.csv.

Setup:   pip install pyserial matplotlib
Usage:   python led_logger.py <serial_port> <led_name>
Example: python led_logger.py /dev/cu.usbserial-0001 red
         python led_logger.py COM3 blue

Turn the pot slowly from 0 V up to full while it runs. Press Ctrl+C to stop
and save. Close the Arduino Serial Monitor first - only one program can use
the port at a time.
"""

import csv
import sys

import matplotlib.pyplot as plt
import serial

if len(sys.argv) != 3:
    print(__doc__)
    sys.exit(1)

port, led_name = sys.argv[1], sys.argv[2]
ser = serial.Serial(port, 115200, timeout=1)

volts, amps, rows = [], [], []

plt.ion()
fig, ax = plt.subplots()
points, = ax.plot([], [], ".", markersize=4)
ax.set_xlabel("LED voltage (V)")
ax.set_ylabel("LED current (mA)")
ax.set_title(f"I-V curve: {led_name} LED")
ax.grid(True, alpha=0.3)

print(f"Logging {led_name} LED on {port}. Ctrl+C to stop.")
try:
    while plt.fignum_exists(fig.number):
        line = ser.readline().decode(errors="ignore").strip()
        parts = line.split(",")
        if len(parts) != 3:
            continue
        try:
            t_ms, v_mv, i_ma = int(parts[0]), float(parts[1]), float(parts[2])
        except ValueError:
            continue  # skips the header line and any garbled data

        rows.append((t_ms, v_mv / 1000, i_ma))
        volts.append(v_mv / 1000)
        amps.append(i_ma)

        if len(rows) % 5 == 0:  # redraw every 5 points to keep it responsive
            points.set_data(volts, amps)
            ax.relim()
            ax.autoscale_view()
            plt.pause(0.001)
except KeyboardInterrupt:
    pass
finally:
    ser.close()
    out = f"{led_name}.csv"
    with open(out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["t_ms", "V_led_V", "I_mA"])
        writer.writerows(rows)
    print(f"Saved {len(rows)} points to {out}")
    plt.ioff()
    plt.show()
