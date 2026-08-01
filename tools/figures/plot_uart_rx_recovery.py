#!/usr/bin/env python3
"""Why a single UART error kills the drive MCU's receive path — and the fix.

The MCU's RX is interrupt-driven and *self-perpetuating*: every completed byte
re-arms the next one. That works until the peripheral raises an error, at which
point ST's HAL aborts the reception and hands control to a weak, empty
HAL_UART_ErrorCallback. Nothing re-arms, so RX stops permanently — while TX
keeps streaming telemetry at 100 Hz, which makes the MCU look alive and the
Jetson look at fault.

    python3 tools/figures/plot_uart_rx_recovery.py

Output: assets/figures/uart_rx_recovery.svg
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from buddy_calcs import P  # noqa: E402
from blockdiagram import Canvas  # noqa: E402
from palette import BLUE, CRITICAL, GREEN, GRID, MUTED  # noqa: E402

W, H = 1360, 946
X = [60, 322, 584, 846, 1108]      # five columns
BW, BH = 212, 90
LANE = [168, 432, 700]             # y of each lane's boxes


def lane_label(c: Canvas, y: float, tag: str, text: str, color: str) -> None:
    c.section(60, y - 34, tag, color=color)
    c.label(60 + 26 + len(tag) * 6.6, y - 34, text, size=10.2, color=MUTED)


def main() -> int:
    hz = P["firmware"]["telemetry_hz"]

    c = Canvas(
        W, H,
        title="UART receive is a self-re-arming loop — and one error breaks it open",
        subtitle="Drive MCU (STM32G474, USART2 → ST-LINK VCP). The receive path only "
                 "survives because each completed byte arms the next; an error exits "
                 "that loop and nothing puts it back.")

    # ---------------------------------------------------------------- lane A --
    lane_label(c, LANE[0], "A", "NORMAL BYTE — the loop closes, so RX continues forever",
               GREEN)
    a = [
        c.box(X[0], LANE[0], BW, BH, "byte arrives", "PA3 / USART2_RX",
              ["from the Jetson"], accent=BLUE),
        c.box(X[1], LANE[0], BW, BH, "USART2_IRQHandler", "hw.c",
              ["vector fires"], accent=BLUE),
        c.box(X[2], LANE[0], BW, BH, "HAL_UART_IRQHandler", "ST HAL",
              ["decodes the cause"], accent=BLUE),
        c.box(X[3], LANE[0], BW, BH, "HAL_UART_RxCpltCallback", "ours",
              ["push to rx_ring"], accent=BLUE),
        c.box(X[4], LANE[0], BW, BH, "HAL_UART_Receive_IT", "re-arm",
              ["ready for next byte"], accent=GREEN),
    ]
    for i in range(4):
        c.edge(a[i].r(), a[i + 1].l(), color=BLUE)
    # the loop that makes RX self-sustaining
    c.edge(a[4].b(), a[0].b(), label="arms the next byte", color=GREEN,
           via=[(a[4].cx, LANE[0] + BH + 46), (a[0].cx, LANE[0] + BH + 46)],
           label_at=0.5, label_dy=-7)

    # ---------------------------------------------------------------- lane B --
    lane_label(c, LANE[1], "B", "ERROR TODAY — the loop is exited and never re-entered",
               CRITICAL)
    b = [
        c.box(X[0], LANE[1], BW, BH, "byte arrives", "with ORE / FE / NE",
              ["overrun, framing,", "or noise"], accent=CRITICAL),
        c.box(X[1], LANE[1], BW, BH, "USART2_IRQHandler", "hw.c",
              ["vector fires"], accent=BLUE),
        c.box(X[2], LANE[1], BW, BH, "HAL_UART_IRQHandler", "ST HAL",
              ["sets ErrorCode,", "ABORTS the reception"], accent=CRITICAL),
        c.box(X[3], LANE[1], BW, BH, "HAL_UART_ErrorCallback", "weak, EMPTY",
              ["default does nothing"], accent=CRITICAL),
        c.box(X[4], LANE[1], BW, BH, "RX is dead", "permanently",
              ["nothing re-arms"], accent=CRITICAL, fill="#fdf3f3"),
    ]
    for i in range(4):
        c.edge(b[i].r(), b[i + 1].l(), color=CRITICAL if i in (0, 2, 3) else BLUE)
    c.label(X[3] + 96, LANE[1] + BH + 30, "↑ no return arrow — that absence is the bug",
            size=10, color=CRITICAL)

    # the deceptive part: TX is untouched
    tx = c.box(X[2], LANE[1] + BH + 74, BW + 262 + 50, 62,
               f"meanwhile TX is completely unaffected — telemetry keeps flowing at {hz} Hz",
               "", ["so the MCU looks healthy and the Jetson looks at fault; the real "
                    "symptom is that commands stop being obeyed"],
               accent=MUTED, title_size=11.5, mono_rows=False)
    c.edge(b[2].b(), tx.t(0.18), color=MUTED, dash=True, label="TX path", arrow=False)

    # ---------------------------------------------------------------- lane C --
    lane_label(c, LANE[2], "C", "WITH THE FIX — the callback closes the loop again",
               GREEN)
    d = [
        c.box(X[0], LANE[2], BW, BH, "byte arrives", "with ORE / FE / NE",
              ["same fault"], accent=CRITICAL),
        c.box(X[1], LANE[2], BW, BH, "USART2_IRQHandler", "hw.c",
              ["vector fires"], accent=BLUE),
        c.box(X[2], LANE[2], BW, BH, "HAL_UART_IRQHandler", "ST HAL",
              ["sets ErrorCode,", "aborts the reception"], accent=CRITICAL),
        c.box(X[3], LANE[2], BW, BH, "HAL_UART_ErrorCallback", "OURS",
              ["clear ORE/FE/NE/PE"], accent=GREEN),
        c.box(X[4], LANE[2], BW, BH, "HAL_UART_Receive_IT", "re-armed",
              ["RX alive again"], accent=GREEN),
    ]
    for i in range(4):
        c.edge(d[i].r(), d[i + 1].l(),
               color=CRITICAL if i in (0, 2) else (GREEN if i == 3 else BLUE))
    c.edge(d[4].b(), d[0].b(), label="loop restored", color=GREEN,
           via=[(d[4].cx, LANE[2] + BH + 46), (d[0].cx, LANE[2] + BH + 46)],
           label_at=0.5, label_dy=-7)

    # ------------------------------------------------------------------ keys --
    c.rule(60, H - 92, W - 60, color=GRID)
    c.legend(60, H - 68, [
        (BLUE, "normal interrupt flow"),
        (GREEN, "re-arms RX — the loop closes here"),
        (CRITICAL, "error path / dead end"),
    ], gap=15)
    c.note(560, H - 68, [
        "ORE = overrun (a byte arrived before the last was read) · FE = framing · NE = noise",
        "Losing the byte is fine — the protocol parser resynchronises on the 0xB5DD sync word.",
        "Losing the RECEIVER is not: it never recovers, and only a power cycle brings it back.",
    ], size=9.6)
    c.label(60, H - 20,
            "firmware/drive_mcu/src/hw.c · drive_protocol.md · REQ_SAFE_002",
            size=9.7, color=MUTED)

    out = REPO / "assets" / "figures" / "uart_rx_recovery.svg"
    c.save(out)
    print(f"wrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
