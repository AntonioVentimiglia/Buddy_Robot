/* Host tests for the drive MCU safety state machine (no hardware, no HAL).
 * Run via tools/run_protocol_tests.sh, or directly:
 *   cc -Wall -Wextra -Werror -I../src -I../../shared_protocol/buddy_protocol \
 *      ../src/state_machine.c ../../shared_protocol/buddy_protocol/buddy_protocol.c \
 *      test_state_machine.c -o /tmp/tsm && /tmp/tsm
 */
#include <stdio.h>

#include "state_machine.h"

static int failures = 0;
#define CHECK(cond, name)                                       \
    do {                                                        \
        if (cond) { printf("ok   %s\n", name); }                \
        else { printf("FAIL %s\n", name); failures++; }         \
    } while (0)

int main(void) {
    sm_t sm;
    const int16_t v[4] = {500, -500, 500, -500};
    const int16_t big[4] = {9000, 0, 0, 0};

    sm_init(&sm, 750, 200);
    CHECK(sm.state == BP_STATE_SELF_TEST, "boots into SELF_TEST");
    CHECK(!sm_motion_allowed(&sm), "no motion in SELF_TEST");

    sm_self_test_done(&sm, 1);
    CHECK(sm.state == BP_STATE_SAFE_IDLE, "self-test pass -> SAFE_IDLE");

    CHECK(!sm_handle_cmd_vel(&sm, v, 1, 0), "CMD_VEL rejected in SAFE_IDLE");
    sm_handle_mode(&sm, BP_MODE_ARM);
    CHECK(sm.state == BP_STATE_ARMED, "ARM request honored");
    CHECK(sm_handle_cmd_vel(&sm, v, 2, 10), "first CMD_VEL accepted");
    CHECK(sm.state == BP_STATE_ACTIVE && sm_motion_allowed(&sm),
          "ARMED -> ACTIVE on first command");
    CHECK(sm.cmd_seq_echo == 2, "seq echo tracks accepted command");

    sm_handle_cmd_vel(&sm, big, 3, 20);
    CHECK(sm.target_mmps[0] == 750, "velocity clamped to firmware limit");

    /* Watchdog: 200 ms without a command stops motion (REQ_SAFE_002). */
    sm_tick(&sm, 219);
    CHECK(sm.state == BP_STATE_ACTIVE, "alive just inside the timeout");
    sm_tick(&sm, 221);
    CHECK(sm.state == BP_STATE_SAFE_IDLE && (sm.fault_bits & BP_FAULT_CMD_TIMEOUT)
              && sm.target_mmps[0] == 0,
          "watchdog stop at 200 ms, targets zeroed");

    /* Recover, then hardware fault latches. */
    sm_handle_mode(&sm, BP_MODE_ARM);
    sm_handle_cmd_vel(&sm, v, 4, 300);
    sm_raise_fault(&sm, BP_FAULT_OVERCURRENT);
    CHECK(sm.state == BP_STATE_FAULT && !sm_motion_allowed(&sm),
          "hardware fault -> FAULT, motion inhibited");
    sm_handle_mode(&sm, BP_MODE_ARM);
    CHECK(sm.state == BP_STATE_FAULT, "cannot arm out of FAULT");
    sm_handle_mode(&sm, BP_MODE_CLEAR_FAULT);
    CHECK(sm.state == BP_STATE_SAFE_IDLE && sm.fault_bits == 0,
          "explicit CLEAR_FAULT recovers");

    /* E-stop dominates everything, and release alone is not enough. */
    sm_set_estop(&sm, 1);
    CHECK(sm.state == BP_STATE_FAULT && (sm.fault_bits & BP_FAULT_ESTOP),
          "E-stop -> FAULT");
    sm_handle_mode(&sm, BP_MODE_CLEAR_FAULT);
    CHECK(sm.state == BP_STATE_FAULT, "E-stop blocks CLEAR_FAULT while active");
    sm_set_estop(&sm, 0);
    CHECK(sm.state == BP_STATE_FAULT, "E-stop release does not auto-run");
    sm_handle_mode(&sm, BP_MODE_CLEAR_FAULT);
    CHECK(sm.state == BP_STATE_SAFE_IDLE, "recovery after release + clear");

    /* Failed self-test never reaches SAFE_IDLE. */
    sm_init(&sm, 750, 200);
    sm_self_test_done(&sm, 0);
    CHECK(sm.state == BP_STATE_FAULT && (sm.fault_bits & BP_FAULT_INTERNAL),
          "failed self-test -> FAULT");

    /* CMD_TIMEOUT must not latch.
     *
     * sm_tick() documents the watchdog as "a recoverable stop, not a latched
     * fault" and drops to SAFE_IDLE rather than FAULT. But the bit it sets had
     * no clear path: MODE_CLEAR_FAULT only acts in FAULT state, which the
     * watchdog deliberately avoids, so once set the bit was unreachable and
     * every later transition reported a fault that had already been recovered.
     * Found on real hardware - a fresh run inherited 0x0002 from the previous
     * session and reported it in ARMED and ACTIVE.
     * ESTOP already had this right (sm_set_estop clears its bit on release);
     * this asserts CMD_TIMEOUT behaves the same way. */
    {
        int16_t v[4] = {100, 100, 100, 100};
        sm_init(&sm, 750, 200);
        sm_self_test_done(&sm, 1);
        sm_handle_mode(&sm, BP_MODE_ARM);
        CHECK(sm_handle_cmd_vel(&sm, v, 1, 1000) && sm.state == BP_STATE_ACTIVE,
              "timeout-recovery: reached ACTIVE");

        sm_tick(&sm, 1000 + 201); /* let the watchdog expire */
        CHECK(sm.state == BP_STATE_SAFE_IDLE &&
              (sm.fault_bits & BP_FAULT_CMD_TIMEOUT),
              "timeout-recovery: watchdog stops to SAFE_IDLE and flags timeout");

        sm_handle_mode(&sm, BP_MODE_ARM);
        CHECK(sm.state == BP_STATE_ARMED &&
              !(sm.fault_bits & BP_FAULT_CMD_TIMEOUT),
              "timeout-recovery: re-ARM clears the stale timeout bit");

        CHECK(sm_handle_cmd_vel(&sm, v, 2, 2000) &&
              sm.fault_bits == 0 && sm.state == BP_STATE_ACTIVE,
              "timeout-recovery: driving again leaves no residual fault bits");
    }

    printf(failures ? "\n%d FAILURES\n" : "\nall state machine tests passed\n",
           failures);
    return failures ? 1 : 0;
}
