#!/usr/bin/env python3
'''Battery sizing helper for Buddy.'''


def required_wh(average_power_w, runtime_hours, usable_fraction=0.8, conversion_efficiency=0.9):
    return average_power_w * runtime_hours / usable_fraction / conversion_efficiency


def peak_current(peak_power_w, pack_voltage_v):
    return peak_power_w / pack_voltage_v


if __name__ == "__main__":
    print("Example required Wh:", required_wh(180, 1.0))
    print("Example peak current A:", peak_current(600, 24))
