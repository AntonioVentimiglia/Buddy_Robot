# Chassis Interface — What CAD Owns, and What It Must Obey

**Created:** 2026-08-01 · **Status:** contract, in force from the first chassis model

The chassis is the first part of Buddy designed in CAD rather than in
`design_params.yaml`. That creates a risk the rest of the repo does not have:
**two sources of truth for the same number** — the YAML the URDF, Gazebo, and the
torque envelope believe, versus the SolidWorks model you actually build and
print. When those drift, nothing errors. The simulation is simply describing a
robot that does not exist.

This document exists so that cannot happen quietly.

> This is the same failure class as the hand-drawn Mermaid diagram deleted on
> 2026-07-28 (it showed a CAN bridge two weeks after ADR-0006 chose USB serial)
> and the `0.08 m` wheel radius found in the deleted CAN stubs. Neither was
> caught by review. Both were caught by something mechanical.

---

## The rule

**`design_params.yaml` stays the single source of truth. CAD is downstream of
it, and reports exactly three things back.**

The build does **not** parse SolidWorks files. You read mass properties and type
the numbers in. That is a *measurement*, no different from "verify wheel mass on
receipt" — and it keeps the parametric chain intact without a fragile CAD
integration.

---

## 1. Interface parameters — owned by the YAML, CAD must satisfy them

Changing any of these is a **design decision made in `design_params.yaml`** and
pushed out to CAD. Never the reverse.

| Parameter | Where | Why it is not CAD's to choose |
|---|---|---|
| `wheels.y_offset_m` | half the track | Sets the pivot-scrub moment arm. The carpet-pivot torque that justified the 5203 motors (ADR-0003) is computed from it — change it and the motor selection needs re-checking. |
| `wheels.x_offset_m` | wheelbase/2 | Same: the wheelbase/track ratio drives skid-steer scrub. |
| `wheels.radius_m` | 0.048 m | Locked by ADR-0004. Also fixes axle height, since `base_center_z` is derived as `radius − z_offset` so wheels touch ground in sim. |
| `chassis.length_m/width_m/height_m` | bounding box | Feeds the URDF collision box and Nav2's footprint. CAD may use **less** than this envelope; it may not exceed it without a YAML edit. |
| ground clearance | derived | Requirement, amended to 0.038 m in ADR-0004. Checked on every build. |

**If CAD cannot meet one of these, that is a finding, not a workaround.** Edit
the YAML, run `python3 tools/build.py`, read what the validators say, and record
the change — the pivot torque and ground-clearance checks exist precisely to
catch this.

---

## 2. Measured properties — owned by CAD, typed back into the YAML

| Field | From | Effect when filled |
|---|---|---|
| `chassis.mass_kg` | SolidWorks mass properties | Real gross mass instead of the 18 kg placeholder |
| `chassis.mass_source` | you | `placeholder` → `cad` → `weighed`. Provenance, not a value |
| `chassis.com_m` | mass properties, relative to `base_link` origin | URDF gets a real inertial origin |
| `chassis.inertia_kgm2` | mass properties, **about the CoM** | URDF gets the real tensor, products of inertia included |

**Both `com_m` and `inertia_kgm2` are `null` until CAD measures them.** While
null the URDF falls back to a uniform solid-box approximation about the
geometric centre — the behaviour it has always had. Filling them flips
`measured_inertia` to true in the generated `buddy_params.xacro` and the
simulation inherits the real mass distribution.

The generator **refuses a partially-filled tensor** rather than silently zeroing
the missing components:

```
chassis com_m/inertia_kgm2 are partially filled — missing ['ixy', 'ixz', 'iyz'].
Fill every component or set both back to null; a half-measured inertia is worse
than an honest box approximation.
```

### Why the CoM matters more than the mass

The 20° ramp requirement is a **tipping** problem, and tipping depends on where
the mass sits, not how much there is. The box approximation assumes the centre
of mass is at the geometric centre of the shell — which will be wrong the moment
a ~2.1 kg LiFePO4 pack goes anywhere other than dead centre. Until `com_m` is
filled, **the simulation cannot tell you anything trustworthy about tipping.**

---

## 3. CAD's own business — keep it out of the YAML

Everything not listed above belongs to CAD alone and must **not** be mirrored
into `design_params.yaml`: rib layout and wall thickness, fillets and chamfers,
mounting bosses and heat-set insert positions, cable routing, print orientation
and part splits, fastener sizes and patterns, tolerances and clearances.

If a number is not consumed by the URDF, the torque analysis, the power model, or
a requirement, it does not go in the YAML.

---

## 4. Workflow

1. **Decide the interface numbers in `design_params.yaml` first.** Track,
   wheelbase, bounding box. This is where design conflict #2 (0.3 × 0.3 m
   footprint vs 20 kg + 10 kg payload + arms) gets resolved.
2. `python3 tools/build.py` — confirm the validators pass at the new geometry
   *before* modelling to it.
3. **Model in SolidWorks to those numbers.**
4. Read **mass properties**; type `mass_kg`, `com_m`, `inertia_kgm2` back in and
   set `mass_source: cad`.
5. `python3 tools/build.py` again. URDF, figures, and torque sweep follow.
6. Commit CAD and the YAML change **together**, so the model and the numbers
   that describe it are never separated in history.

---

## 5. Open item — the mass budget just got tighter

The torque envelope is computed at the **20 kg design ceiling**, so drive sizing
is valid as long as the finished robot stays under it. Two decisions have since
eaten into that headroom:

- **ADR-0005 amendment (2026-08-01):** LiFePO4 costs **≈ +1.3 kg** over the
  3S Li-ion it replaced — more than the +0.6–0.8 kg the 2026-07-14 amendment
  absorbed.
- **ADR-0008:** printed structure is heavier than machined aluminium for the
  same stiffness.

**Chassis CAD is where this stops being an assumption.** The first real
`mass_kg` out of SolidWorks is the number that says whether the 20 kg ceiling
still holds — and if it does not, the honest responses are to cut mass, raise
the ceiling and re-run the torque envelope, or revisit the chemistry. Not to
quietly exceed it.
