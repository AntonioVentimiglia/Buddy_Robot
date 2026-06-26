# Drive Torque Sizing

Use this before selecting motors.

## Inputs

| Variable | Meaning | Value |
|---|---|---|
| `m` | total robot mass including payload | TBD kg |
| `r` | wheel radius | TBD m |
| `a` | desired acceleration | TBD m/s^2 |
| `theta` | ramp angle | TBD deg |
| `Crr` | rolling resistance coefficient | TBD |
| `n` | number of driven wheels | 4 assumed |
| `eta` | drivetrain efficiency | 0.70-0.85 placeholder |
| `SF` | safety factor | 1.5-2.5 placeholder |

## Formula

```text
F = m*a + m*g*sin(theta) + Crr*m*g*cos(theta)
T_wheel = (F * r / n) * SF / eta
wheel_rpm = (v / (2*pi*r)) * 60
```

## Four-wheel differential note

Skid steering can consume extra current during turning. Add margin for tire scrub, carpet, ramps, payload, and future arm mass.
