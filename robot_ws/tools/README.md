# Tools

Start with `torque_sweep.py`. It estimates torque per driven output and wheel RPM for candidate wheel radius, mass, ramp, and speed.

Example:

```bash
python3 tools/torque_sweep.py --mass-kg 30 --wheel-radius-m 0.06 --driven-wheels 4 --speed-mps 1.5 --ramp-deg 20 --csv analysis/torque_sweep.csv
```
