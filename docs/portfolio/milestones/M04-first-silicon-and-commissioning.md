---
title: "M04 — First Silicon: From \"It Compiles\" to a Commissioned Link"
date: 2026-07-31
type: milestone
tags: [embedded, firmware, software, test, process]
summary: The drive firmware leaves the host-test bubble and runs on a real STM32G474 — 102 Hz telemetry, 0.49 ms round trip, and the ROS bridge driving the real state machine. Running it on hardware immediately exposed a latched-fault bug that twenty passing host tests could not.
figures: [assets/figures/fault_state_machine.svg, assets/figures/startup_sequence.svg]
---

# M04 — First Silicon: From "It Compiles" to a Commissioned Link

For two weeks the strongest true statement about Buddy's drive firmware was
*it compiles*. 16.4 kB for a NUCLEO-G474RE, a pure-C safety state machine with
twenty passing host assertions, a wire protocol implemented twice and pinned
byte-for-byte by golden vectors, and a mock MCU thorough enough that the
Jetson-side bridge had been integration-tested end to end without a single
purchased component.

All of it had never executed one instruction on an STM32.

This milestone closes that gap. It also demonstrates why the gap mattered: the
first two hours on real hardware surfaced a firmware bug that the entire
host-test suite was structurally incapable of catching.

## What was commissioned

| Layer | Evidence |
|---|---|
| Jetson runtime | ROS 2 Jazzy installed, workspace builds (3 packages, 5.5 s) |
| Firmware on silicon | Flashed and verified; board self-identifies as `STM32G47x_G48x`, ST-LINK V3J16 |
| Device naming | `0483:374e` matched the udev rule; `/dev/buddy_drive_mcu` appeared on first plug-in |
| Wire link | 102.0 Hz telemetry (100 Hz target), **0 CRC errors** across 204 frames |
| Round trip | PING→PONG **0.48–0.61 ms**, median 0.49 |
| Safety state | Boots `SELF_TEST → SAFE_IDLE`, never enters ACTIVE unprompted |
| ROS integration | Bridge drives the real MCU: `cmd_seq_echo=71` |
| Watchdog | Fired on silicon after commands stopped — `fault_bits=0x0002` |

The round-trip number is the one worth dwelling on. The
[interface verification](../../system_model/electrical_interfaces.md) argued on
paper that the ST-LINK VCP had ~18× bandwidth margin. Measured, the latency
margin against the 200 ms watchdog (REQ_SAFE_002) is roughly **330×**. The link
is nowhere near being the constraint on this bus — which retires a risk that had
been carried on an estimate since ADR-0006.

Equally important is what the numbers are *not*. With no encoders attached,
`wheel_pos` stays at zero, so `/odom` does not advance no matter what is
commanded. That is correct behaviour, not a defect, and the verification script
says so explicitly rather than quietly asserting something it cannot prove.

## The bug that only hardware could find

`sm_tick` implements the command watchdog. It carries this comment:

> *per state_machine.md: timeout is a recoverable stop, not a latched fault*

and it behaves accordingly — on timeout it zeroes the wheel targets and drops to
`SAFE_IDLE` rather than `FAULT`. One line above that comment, it sets
`BP_FAULT_CMD_TIMEOUT`.

Nothing anywhere cleared that bit. `MODE_CLEAR_FAULT` only acts when the state
machine is in `FAULT` — precisely the state the watchdog deliberately avoids.
Once set, the bit was unreachable for the remaining life of the MCU. The
implementation contradicted its own stated design intent, one line apart.

**How it surfaced.** The bridge was run against real silicon twice. The second
run inherited `0x0002` from the first and reported it during `ARMED` and again
during `ACTIVE` — a stale flag from a previous session masquerading as a live
fault. Worse, a genuinely new timeout would have been indistinguishable from it.

**Why the host tests missed it.** Every state-machine test begins at `sm_init`,
with `fault_bits = 0`. The bug is only observable across a *session boundary* —
recover from a timeout, then look at what you inherited. Twenty assertions
covering E-stop dominance, arm-out-of-fault refusal, and watchdog timing all
passed, because none of them asked that question. This is the specific value of
running on hardware: not that hardware is more rigorous, but that it does not
share the test suite's assumptions about where a story starts.

**The codebase already knew the answer.** `sm_set_estop` clears its own bit when
the E-stop is released. The correct behaviour was already written down, in the
same file, for the adjacent condition. `CMD_TIMEOUT` now follows the same
pattern — cleared on re-ARM and on any accepted `CMD_VEL`, and only that bit;
real faults still require an explicit `CLEAR_FAULT` from `FAULT` state.

The fix was written test-first: four assertions added, **confirmed failing**
against the old firmware, then the change. `mock_mcu.py` carried the identical
defect — it mirrors the C state machine faithfully, bug included — so it was
fixed in the same commit. Keeping those two implementations in lockstep is the
entire reason the protocol was written twice.

Verification was by repetition rather than assertion: the hardware check was run
twice in succession. Run 1 leaves a watchdog timeout behind; run 2 came up clean.

## A second bug: the bridge cried wolf

The bridge logged every `FAULT_EVT` frame at `WARN` as "MCU fault event". But
`FAULT_EVT` is emitted on *any* state transition — `main.c` sends it whenever
state or fault bits change, and `drive_protocol.md` documents it as "on
transition". The first real run duly reported two "faults" that were the benign
`SAFE_IDLE → ARMED` handover with `bits=0x0000`.

Left alone this would have made the bench phase wall-to-wall spurious warnings,
with real faults invisible among them — the classic path to an operator who has
learned to ignore the log. It now warns only when a fault bit is actually set.

A second defect hid in the same handler: it reported `core.state_name()` —
whatever the most recent telemetry frame happened to say — rather than the state
carried in the event payload that the transition was actually about.

## What went wrong

Four failures in one session, and the ratio is the interesting part: **three of
them were in the instrument, not the system.**

1. **The setup script had never been run end to end.** `set -euo pipefail` plus
   ROS's own `setup.bash`, which reads variables it never sets, is fatal under
   `-u`. The script died at step 3 of 6 — after a fifteen-minute `apt` install,
   on the first line that costs nothing.
2. **A 37% velocity shortfall that was a measurement window.** Node startup, DDS
   discovery, the arm transition and the mock's wheel ramp all landed inside the
   sample period. It had the same *shape* as the 4× encoder scaling bug found on
   16 July, which is exactly why it was worth chasing properly instead of
   assuming either way.
3. **A 99–111 ms "round trip" that was `read(512)` refusing to return** until 512
   bytes accumulated — about 110 ms at this telemetry rate. Reading `in_waiting`
   moved the number to 0.49 ms.
4. **A PING/PONG failure that sent me into the HAL.** I checked `volatile` on the
   RX ring (correct), noticed there is no `HAL_UART_ErrorCallback`, and theorised
   that a DTR transient on port-open had latched a UART error and killed RX. A
   controlled experiment — quiesce DTR/RTS, reset the MCU with the port already
   open, re-ping — returned 5/5 both before and after, refuting it. The real
   cause was my script asserting `PONG.seq == PING.seq`, which the spec never
   defines.

The pattern worth internalising: **when a measurement disagrees with a design
estimate by two orders of magnitude, falsify the measurement first.** It is
cheaper, and here it was right three times out of four. The verification scripts
are newer and far less exercised than the code they test, so for now a failing
check deserves suspicion before the system does.

That said, item 4 produced a real finding as a by-product. The missing
`HAL_UART_ErrorCallback` is genuine: nothing re-arms `HAL_UART_Receive_IT` after
a UART error, so a single overrun would silently kill RX while telemetry
continued streaming outward — a failure that presents as a dead Jetson link
rather than a dead MCU. It was not the cause of this bug, so it was logged as a
bench item rather than fixed blind.

## Process: the milestone as a script

Each of these checks is a committed script with written pass/fail criteria
rather than a procedure someone follows in three terminals:

- `devops/jetson/verify_zero_hardware_stack.sh` — 9/9, bridge against the mock
- `devops/jetson/verify_drive_mcu_link.py` — 13/13, protocol against real silicon
- `devops/jetson/verify_bridge_vs_real_mcu.sh` — 13/13, ROS through to hardware

The reason is visible in this milestone's own history: the *same* check was run
before and after a firmware change, and the difference between the runs is the
evidence that the fix worked. A procedure in a wiki cannot be re-run to prove a
regression did not happen.

The robot also stopped depending on a particular laptop. The Jetson holds its own
GitHub deploy key and pulls directly, so the workflow from any machine is
`ssh buddy 'cd ~/Buddy_Robot && git pull'` — which matters now that firmware,
verification scripts and ROS packages all have to move together.

## Where this leaves the project

The drive stack is commissioned from `/cmd_vel` down to a real STM32 register,
with every layer measured rather than assumed. What remains before the bench
drive loop is genuinely blocked on the goBILDA shipment: motors, encoders and the
mechanical parts to hold them.

Not blocked, and next: the `HAL_UART_ErrorCallback` fix (inducible and testable
on the board already in hand), velocity PID against a plant model derived from
the 5203 datasheet, and a quadrature rig built from the spare NUCLEO to validate
the 753.2 counts/rev decoding — the exact number the encoder bug got wrong, and
one the vendor datasheet states incorrectly — before any motor arrives to test it
with.
