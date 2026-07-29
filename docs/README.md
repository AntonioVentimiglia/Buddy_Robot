# Documentation

This folder contains the design model for Buddy: requirements, system architecture, interface contracts, frame tree, power and safety planning, hardware decisions, and reference material. These docs are as important as code because they preserve assumptions while hardware is still changing.

Start here:

1. `system_model/system_integration.md` — the six generated integration figures
   and both KiCAD sheets, indexed. Fastest way to see how the robot fits together.
2. `requirements/buddy_v0_1_requirements.yaml`
3. `requirements/design_conflicts.md`
4. `system_model/architecture_overview.md`
5. `system_model/frame_tree.md`
6. `system_model/interface_contract.md`
7. `decisions/ADR-0001-ros2-jetpack-baseline.md`

`system_model/integration_map.yaml` is a source file, not prose: it holds the
system's **topology** (nodes, topics, buses, rails, nets, states) and is the
input to the integration figures and to the build's drift checker. Edit it and
re-run `python3 tools/build.py`.
