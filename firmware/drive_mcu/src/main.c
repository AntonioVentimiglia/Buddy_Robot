/* Buddy drive MCU — main superloop.
 *
 * Architecture: docs/state_machine.md + firmware/shared_protocol/drive_protocol.md.
 * The safety core (state_machine.c) and the wire protocol (buddy_protocol.c)
 * are pure C and host-tested; this file glues them to hw.c at the rates set in
 * buddy_config.h (generated from design_params.yaml by tools/build.py).
 *
 * Skeleton status (compiles; bench items marked):
 *   - Open-loop duty from velocity target; velocity PID lands at bench phase
 *     once motor constants are measured (encoder feedback already flows).
 *   - Current limit: per-wheel PWM cut above BUDDY_CURRENT_LIMIT_MA, refined
 *     to mid-pulse sampling + faster loop at bench (electrical_interfaces.md).
 */
#include "buddy_config.h"
#include "buddy_protocol.h"
#include "hw.h"
#include "state_machine.h"

#define FW_MAJOR 0
#define FW_MINOR 1
#define FW_PATCH 0

static sm_t sm;
static bp_parser_t parser;
static uint8_t tx_seq;

static uint8_t next_seq(void) { return ++tx_seq; }

static void send_frame(uint8_t type, const uint8_t *payload, uint8_t len) {
    uint8_t buf[BP_MAX_PAYLOAD + BP_OVERHEAD];
    size_t n = bp_encode(buf, sizeof buf, type, next_seq(), payload, len);
    if (n) hw_uart_write(buf, (int)n);
}

static void send_fault_evt(void) {
    uint8_t pl[3];
    bp_pack_u16(&pl[0], sm.fault_bits);
    pl[2] = sm.state;
    send_frame(BP_T_FAULT_EVT, pl, 3);
}

static void handle_frame(const bp_frame_t *f, uint32_t now) {
    switch (f->type) {
    case BP_T_CMD_VEL:
        if (f->len == 8) {
            int16_t v[4];
            for (int i = 0; i < 4; i++) v[i] = bp_unpack_i16(&f->payload[2 * i]);
            sm_handle_cmd_vel(&sm, v, f->seq, now);
        }
        break;
    case BP_T_CMD_MODE:
        if (f->len == 1) sm_handle_mode(&sm, f->payload[0]);
        break;
    case BP_T_PING: {
        uint8_t pl[4] = {FW_MAJOR, FW_MINOR, FW_PATCH, BP_VERSION};
        send_frame(BP_T_PONG, pl, 4);
        break;
    }
    default:
        break;
    }
}

static void send_telemetry(void) {
    bp_telemetry_t t;
    t.state = sm.state;
    t.fault_bits = sm.fault_bits;
    t.estop = sm.estop;
    t.cmd_seq_echo = sm.cmd_seq_echo;
    for (int i = 0; i < 4; i++) {
        t.wheel_pos[i] = hw_encoder_count(i);
        t.wheel_vel[i] = sm.target_mmps[i]; /* TODO(bench): measured velocity */
        t.motor_cur_ma[i] = (int16_t)hw_motor_current_ma(i);
    }
    t.vbat_mv = hw_vbat_mv();
    uint8_t buf[BP_MAX_PAYLOAD + BP_OVERHEAD];
    size_t n = bp_encode_telemetry(buf, sizeof buf, next_seq(), &t);
    if (n) hw_uart_write(buf, (int)n);
}

static void drive_outputs(void) {
    if (!sm_motion_allowed(&sm)) {
        hw_all_motors_off();
        return;
    }
    for (int i = 0; i < 4; i++) {
        /* current limit: cut this wheel for the rest of the control period */
        if (hw_motor_current_ma(i) > BUDDY_CURRENT_LIMIT_MA) {
            hw_set_motor(i, 0);
            continue;
        }
        /* open-loop skeleton: duty proportional to velocity target */
        int32_t duty = (int32_t)sm.target_mmps[i] * 1000 / BUDDY_VEL_LIMIT_MMPS;
        hw_set_motor(i, duty);
    }
}

int main(void) {
    hw_init();
    bp_parser_init(&parser);
    sm_init(&sm, BUDDY_VEL_LIMIT_MMPS, BUDDY_WATCHDOG_MS);

    /* Self-test: drivers must not report faults with outputs off. */
    hw_all_motors_off();
    int self_ok = 1;
    for (int i = 0; i < 4; i++)
        if (hw_driver_fault(i)) self_ok = 0;
    sm_self_test_done(&sm, self_ok);

    uint32_t last_telem = 0, last_ctrl = 0, last_fault_bits = sm.fault_bits;
    uint8_t last_state = sm.state;
    uint8_t rx[64];
    bp_frame_t frame;

    for (;;) {
        uint32_t now = hw_millis();

        /* E-stop chain state (reporting; hardware cuts power regardless) */
        sm_set_estop(&sm, (uint8_t)hw_estop_active());

        /* protocol input */
        int n = hw_uart_read(rx, sizeof rx);
        for (int i = 0; i < n; i++)
            if (bp_parser_feed(&parser, rx[i], &frame)) handle_frame(&frame, now);

        /* watchdog + driver faults */
        sm_tick(&sm, now);
        for (int i = 0; i < 4; i++)
            if (sm.state == BP_STATE_ACTIVE && hw_driver_fault(i))
                sm_raise_fault(&sm, BP_FAULT_DRIVER);

        /* control loop */
        if (now - last_ctrl >= (1000u / BUDDY_CONTROL_HZ) || now < last_ctrl) {
            last_ctrl = now;
            drive_outputs();
        }

        /* telemetry + fault edge reporting */
        if (now - last_telem >= (1000u / BUDDY_TELEMETRY_HZ)) {
            last_telem = now;
            send_telemetry();
            hw_led(sm.state == BP_STATE_ACTIVE ? 1 : (now >> 9) & 1);
        }
        if (sm.fault_bits != last_fault_bits || sm.state != last_state) {
            last_fault_bits = sm.fault_bits;
            last_state = sm.state;
            send_fault_evt();
        }
    }
}
