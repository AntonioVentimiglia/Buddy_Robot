/* Drive MCU safety state machine — see state_machine.h. */
#include "state_machine.h"

static void stop_targets(sm_t *sm) {
    for (int i = 0; i < 4; i++) sm->target_mmps[i] = 0;
}

void sm_init(sm_t *sm, int16_t vel_limit_mmps, uint32_t watchdog_ms) {
    sm->state = BP_STATE_BOOT;
    sm->fault_bits = 0;
    sm->estop = 0;
    sm->cmd_seq_echo = 0;
    sm->last_cmd_ms = 0;
    sm->vel_limit_mmps = vel_limit_mmps;
    sm->watchdog_ms = watchdog_ms;
    stop_targets(sm);
    sm->state = BP_STATE_SELF_TEST;
}

void sm_self_test_done(sm_t *sm, int ok) {
    if (sm->state != BP_STATE_SELF_TEST) return;
    if (ok) {
        sm->state = BP_STATE_SAFE_IDLE;
    } else {
        sm->fault_bits |= BP_FAULT_INTERNAL;
        sm->state = BP_STATE_FAULT;
    }
}

void sm_handle_mode(sm_t *sm, uint8_t mode) {
    if (sm->estop) return; /* E-stop dominates all mode requests */
    switch (mode) {
    case BP_MODE_ARM:
        if (sm->state == BP_STATE_SAFE_IDLE) sm->state = BP_STATE_ARMED;
        break;
    case BP_MODE_SAFE_IDLE:
        if (sm->state == BP_STATE_ARMED || sm->state == BP_STATE_ACTIVE) {
            stop_targets(sm);
            sm->state = BP_STATE_SAFE_IDLE;
        }
        break;
    case BP_MODE_CLEAR_FAULT:
        if (sm->state == BP_STATE_FAULT) {
            sm->fault_bits = 0;
            stop_targets(sm);
            sm->state = BP_STATE_SAFE_IDLE;
        }
        break;
    default:
        break;
    }
}

static int16_t clamp16(int16_t v, int16_t lim) {
    if (v > lim) return lim;
    if (v < (int16_t)-lim) return (int16_t)-lim;
    return v;
}

int sm_handle_cmd_vel(sm_t *sm, const int16_t vel_mmps[4], uint8_t seq,
                      uint32_t now_ms) {
    if (sm->estop) return 0;
    if (sm->state == BP_STATE_ARMED) sm->state = BP_STATE_ACTIVE;
    if (sm->state != BP_STATE_ACTIVE) return 0;
    for (int i = 0; i < 4; i++)
        sm->target_mmps[i] = clamp16(vel_mmps[i], sm->vel_limit_mmps);
    sm->cmd_seq_echo = seq;
    sm->last_cmd_ms = now_ms;
    return 1;
}

void sm_set_estop(sm_t *sm, uint8_t active) {
    sm->estop = active ? 1u : 0u;
    if (active) {
        sm->fault_bits |= BP_FAULT_ESTOP;
        stop_targets(sm);
        sm->state = BP_STATE_FAULT;
    } else {
        sm->fault_bits &= (uint16_t)~BP_FAULT_ESTOP;
        /* remain in FAULT until an explicit CLEAR_FAULT */
    }
}

void sm_raise_fault(sm_t *sm, uint16_t fault_bits) {
    sm->fault_bits |= fault_bits;
    stop_targets(sm);
    sm->state = BP_STATE_FAULT;
}

void sm_tick(sm_t *sm, uint32_t now_ms) {
    if (sm->state == BP_STATE_ACTIVE &&
        (now_ms - sm->last_cmd_ms) > sm->watchdog_ms) {
        sm->fault_bits |= BP_FAULT_CMD_TIMEOUT;
        stop_targets(sm);
        sm->state = BP_STATE_SAFE_IDLE; /* per state_machine.md: timeout is a
                                           recoverable stop, not a latched fault */
    }
}

int sm_motion_allowed(const sm_t *sm) {
    return sm->state == BP_STATE_ACTIVE && !sm->estop;
}
