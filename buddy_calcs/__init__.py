"""buddy_calcs — single source of truth loader + engineering equations.

Every consumer (marimo notebooks, figure scripts, torque_sweep CLI, the xacro
generator) imports parameters from here so no value is ever duplicated:

    from buddy_calcs import P, R
    from buddy_calcs import drive

P = design choices/assumptions (design_params.yaml)
R = requirements               (docs/requirements/buddy_v0_1_requirements.yaml)
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PARAMS_FILE = ROOT / "design_params.yaml"
REQUIREMENTS_FILE = ROOT / "docs" / "requirements" / "buddy_v0_1_requirements.yaml"


def load() -> tuple[dict, dict]:
    """Reload both YAML sources from disk."""
    params = yaml.safe_load(PARAMS_FILE.read_text())
    reqs = yaml.safe_load(REQUIREMENTS_FILE.read_text())
    return params, reqs


P, R = load()


def base_center_z() -> float:
    """Height of base_link center above ground.

    Derived, never set directly: axle height must equal wheel radius or the
    wheels float/sink in sim.  base_center_z + z_offset = wheel_radius.
    """
    return P["wheels"]["radius_m"] - P["wheels"]["z_offset_m"]


def ground_clearance() -> float:
    """Chassis-bottom height above ground (derived from geometry)."""
    return base_center_z() - P["chassis"]["height_m"] / 2.0


def validate() -> list[str]:
    """Cross-check derived geometry against requirements. Returns problems."""
    problems = []
    req_clear = R["geometry"]["ground_clearance_m"]
    if ground_clearance() + 1e-9 < req_clear:
        problems.append(
            f"derived ground clearance {ground_clearance():.3f} m is below the "
            f"required {req_clear} m (requirements yaml)"
        )
    return problems
