/* Host-side unit tests for the shared C protocol implementation.
 * Build & run (no hardware needed):
 *   cc -Wall -Wextra -Werror -I../buddy_protocol \
 *      ../buddy_protocol/buddy_protocol.c test_protocol.c -o test_protocol && ./test_protocol
 * Also run by tools/run_protocol_tests.sh alongside the Python tests.
 */
#include <stdio.h>
#include <string.h>

#include "buddy_protocol.h"

static int failures = 0;
#define CHECK(cond, name)                                        \
    do {                                                         \
        if (cond) { printf("ok   %s\n", name); }                 \
        else { printf("FAIL %s\n", name); failures++; }          \
    } while (0)

static void feed_all(bp_parser_t *p, const uint8_t *buf, size_t n,
                     bp_frame_t *out, int *got) {
    *got = 0;
    for (size_t i = 0; i < n; i++)
        if (bp_parser_feed(p, buf[i], out)) (*got)++;
}

int main(void) {
    /* CRC-16/CCITT-FALSE known value: "123456789" -> 0x29B1 */
    CHECK(bp_crc16((const uint8_t *)"123456789", 9) == 0x29B1, "crc16 check value");

    /* Golden vector: PING seq=7 */
    uint8_t buf[128];
    size_t n = bp_encode(buf, sizeof buf, BP_T_PING, 7, NULL, 0);
    CHECK(n == 8, "ping frame length");
    CHECK(buf[0] == 0xB5 && buf[1] == 0xDD && buf[2] == 0x01 && buf[3] == 0x03 &&
              buf[4] == 0x07 && buf[5] == 0x00,
          "ping header bytes");
    printf("vector PING seq=7:    ");
    for (size_t i = 0; i < n; i++) printf("%02x", buf[i]);
    printf("\n");

    /* Golden vector: CMD_VEL seq=1 (100,-100,250,-250) */
    int16_t v[4] = {100, -100, 250, -250};
    size_t n2 = bp_encode_cmd_vel(buf, sizeof buf, 1, v);
    CHECK(n2 == 16, "cmd_vel frame length");
    printf("vector CMD_VEL seq=1: ");
    for (size_t i = 0; i < n2; i++) printf("%02x", buf[i]);
    printf("\n");

    /* Round-trip through the parser */
    bp_parser_t p;
    bp_parser_init(&p);
    bp_frame_t f;
    int got;
    feed_all(&p, buf, n2, &f, &got);
    CHECK(got == 1 && f.type == BP_T_CMD_VEL && f.seq == 1 && f.len == 8,
          "cmd_vel parse round-trip");
    CHECK(bp_unpack_i16(&f.payload[0]) == 100 && bp_unpack_i16(&f.payload[2]) == -100 &&
              bp_unpack_i16(&f.payload[4]) == 250 && bp_unpack_i16(&f.payload[6]) == -250,
          "cmd_vel payload values");

    /* Corrupted CRC must be rejected and counted */
    uint8_t bad[16];
    memcpy(bad, buf, n2);
    bad[10] ^= 0xFF;
    feed_all(&p, bad, n2, &f, &got);
    CHECK(got == 0 && p.crc_errors == 1, "corrupt frame rejected");

    /* Garbage + partial syncs + valid frame: parser must resync */
    uint8_t noisy[64];
    size_t k = 0;
    noisy[k++] = 0x00; noisy[k++] = 0xB5; noisy[k++] = 0x11; /* false start */
    noisy[k++] = 0xB5; /* sync0 again */
    memcpy(&noisy[k], buf + 1, n2 - 1); /* rest of a valid frame */
    k += n2 - 1;
    feed_all(&p, noisy, k, &f, &got);
    CHECK(got == 1 && f.type == BP_T_CMD_VEL, "resync through garbage");

    /* Telemetry round-trip */
    bp_telemetry_t t = {.state = BP_STATE_ACTIVE,
                        .fault_bits = BP_FAULT_CMD_TIMEOUT,
                        .estop = 0,
                        .cmd_seq_echo = 42,
                        .wheel_pos = {123456, -123456, 1, -1},
                        .wheel_vel = {750, -750, 100, -100},
                        .motor_cur_ma = {8000, -8000, 500, 0},
                        .vbat_mv = 11100};
    size_t n3 = bp_encode_telemetry(buf, sizeof buf, 9, &t);
    CHECK(n3 == BP_TELEMETRY_LEN + BP_OVERHEAD, "telemetry frame length");
    feed_all(&p, buf, n3, &f, &got);
    bp_telemetry_t r;
    CHECK(got == 1 && bp_decode_telemetry(&f, &r), "telemetry parse");
    CHECK(r.state == t.state && r.fault_bits == t.fault_bits &&
              r.cmd_seq_echo == 42 && r.wheel_pos[0] == 123456 &&
              r.wheel_pos[1] == -123456 && r.wheel_vel[0] == 750 &&
              r.motor_cur_ma[0] == 8000 && r.vbat_mv == 11100,
          "telemetry field round-trip");

    /* Byte-at-a-time delivery (serial reality) already covered by feed_all. */
    printf(failures ? "\n%d FAILURES\n" : "\nall C protocol tests passed\n",
           failures);
    return failures ? 1 : 0;
}
