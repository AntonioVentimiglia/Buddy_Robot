/* Drive MCU safety state machine — pure C, host-testable (no HAL).
 *
 * Implements firmware/drive_mcu/docs/state_machine.md with time injected as
 * millisecond ticks, so the watchdog and every transition are unit-tested on
 * the host (tests/test_state_machine.c) before any hardware exists.
 * States/faults/modes come from the shared protocol header so firmware and
 * wire protocol can never disagree on numbering.
 */
#ifndef STATE_MACHINE_H
#define STATE_MACHINE_H

#include <stdint.h>

#include "buddy_protocol.h"

typedef struct {
    uint8_t state; /* enum bp_state */
    uint16_t fault_bits;
    uint8_t estop;
    uint8_t cmd_seq_echo;
    int16_t target_mmps[4]; /* LF, LR, RF, RR */
    uint32_t last_cmd_ms;
    /* configuration */
    int16_t vel_limit_mmps;
    uint32_t watchdog_ms;
} sm_t;

void sm_init(sm_t *sm, int16_t vel_limit_mmps, uint32_t watchdog_ms);

/* Self-test hook: call once hardware checks pass to leave SELF_TEST. */
void sm_self_test_done(sm_t *sm, int ok);

/* Protocol inputs */
void sm_handle_mode(sm_t *sm, uint8_t mode);
/* Returns 1 if the command was accepted (ARMED/ACTIVE, no estop). */
int sm_handle_cmd_vel(sm_t *sm, const int16_t vel_mmps[4], uint8_t seq,
                      uint32_t now_ms);

/* Environment inputs */
void sm_set_estop(sm_t *sm, uint8_t active);
void sm_raise_fault(sm_t *sm, uint16_t fault_bits);

/* Periodic: enforces the command watchdog. Call at >= 100 Hz. */
void sm_tick(sm_t *sm, uint32_t now_ms);

/* 1 only in ACTIVE with no E-stop — the single gate for PWM output. */
int sm_motion_allowed(const sm_t *sm);

#endif /* STATE_MACHINE_H */
