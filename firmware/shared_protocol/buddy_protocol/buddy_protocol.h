/* Buddy drive protocol v1 — shared C reference implementation.
 *
 * Single source of truth: compiled into the drive MCU firmware AND into
 * host-side unit tests (tests/test_protocol.c). Spec: ../drive_protocol.md.
 * No dependencies beyond <stdint.h>/<stddef.h>; no dynamic allocation.
 */
#ifndef BUDDY_PROTOCOL_H
#define BUDDY_PROTOCOL_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define BP_VERSION 0x01u
#define BP_SYNC0 0xB5u
#define BP_SYNC1 0xDDu
#define BP_MAX_PAYLOAD 64u
#define BP_OVERHEAD 8u /* sync2 + ver + type + seq + len + crc2 */

/* Frame types */
#define BP_T_CMD_VEL 0x01u
#define BP_T_CMD_MODE 0x02u
#define BP_T_PING 0x03u
#define BP_T_TELEMETRY 0x10u
#define BP_T_PONG 0x11u
#define BP_T_FAULT_EVT 0x12u

/* State machine values (mirrors firmware/drive_mcu/docs/state_machine.md) */
enum bp_state {
    BP_STATE_BOOT = 0,
    BP_STATE_SELF_TEST = 1,
    BP_STATE_SAFE_IDLE = 2,
    BP_STATE_ARMED = 3,
    BP_STATE_ACTIVE = 4,
    BP_STATE_FAULT = 5,
    BP_STATE_UPDATE = 6,
};

/* Fault bits */
#define BP_FAULT_ESTOP 0x0001u
#define BP_FAULT_CMD_TIMEOUT 0x0002u
#define BP_FAULT_DRIVER 0x0004u
#define BP_FAULT_OVERCURRENT 0x0008u
#define BP_FAULT_ENCODER 0x0010u
#define BP_FAULT_UNDERVOLT 0x0020u
#define BP_FAULT_OVERTEMP 0x0040u
#define BP_FAULT_INTERNAL 0x8000u

/* CMD_MODE payload values */
#define BP_MODE_SAFE_IDLE 0u
#define BP_MODE_ARM 1u
#define BP_MODE_CLEAR_FAULT 2u

/* CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, no reflection, no xorout. */
uint16_t bp_crc16(const uint8_t *data, size_t n);

/* Encode a frame into buf (capacity cap). Returns total bytes or 0 if it
 * doesn't fit / payload too large. */
size_t bp_encode(uint8_t *buf, size_t cap, uint8_t type, uint8_t seq,
                 const uint8_t *payload, uint8_t len);

/* Incremental resynchronizing parser. Feed bytes one at a time; when a full
 * valid frame is accepted, returns 1 and fills *out. Invalid bytes/frames are
 * dropped (counters incremented) and scanning resumes at the next sync. */
typedef struct {
    uint8_t type;
    uint8_t seq;
    uint8_t len;
    uint8_t payload[BP_MAX_PAYLOAD];
} bp_frame_t;

typedef struct {
    /* internal */
    uint8_t st;
    uint8_t idx;
    bp_frame_t f;
    uint8_t crc_lo;
    /* diagnostics */
    uint32_t crc_errors;
    uint32_t version_errors;
    uint32_t resyncs;
    uint32_t frames_ok;
} bp_parser_t;

void bp_parser_init(bp_parser_t *p);
int bp_parser_feed(bp_parser_t *p, uint8_t byte, bp_frame_t *out);

/* Typed payload helpers (little-endian, no struct packing assumptions). */
void bp_pack_i16(uint8_t *at, int16_t v);
void bp_pack_i32(uint8_t *at, int32_t v);
void bp_pack_u16(uint8_t *at, uint16_t v);
int16_t bp_unpack_i16(const uint8_t *at);
int32_t bp_unpack_i32(const uint8_t *at);
uint16_t bp_unpack_u16(const uint8_t *at);

/* CMD_VEL payload: wheel order LF, LR, RF, RR in mm/s. */
size_t bp_encode_cmd_vel(uint8_t *buf, size_t cap, uint8_t seq,
                         const int16_t vel_mmps[4]);

#define BP_TELEMETRY_LEN 39u
typedef struct {
    uint8_t state;
    uint16_t fault_bits;
    uint8_t estop;
    uint8_t cmd_seq_echo;
    int32_t wheel_pos[4];
    int16_t wheel_vel[4];
    int16_t motor_cur_ma[4];
    uint16_t vbat_mv;
} bp_telemetry_t;

size_t bp_encode_telemetry(uint8_t *buf, size_t cap, uint8_t seq,
                           const bp_telemetry_t *t);
/* Returns 1 on success (frame must be BP_T_TELEMETRY with correct length). */
int bp_decode_telemetry(const bp_frame_t *f, bp_telemetry_t *t);

#ifdef __cplusplus
}
#endif
#endif /* BUDDY_PROTOCOL_H */
