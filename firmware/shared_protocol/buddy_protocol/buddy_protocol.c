/* Buddy drive protocol v1 — implementation. See buddy_protocol.h / spec. */
#include "buddy_protocol.h"

uint16_t bp_crc16(const uint8_t *data, size_t n) {
    uint16_t crc = 0xFFFFu;
    for (size_t i = 0; i < n; i++) {
        crc ^= (uint16_t)data[i] << 8;
        for (int b = 0; b < 8; b++)
            crc = (crc & 0x8000u) ? (uint16_t)((crc << 1) ^ 0x1021u)
                                  : (uint16_t)(crc << 1);
    }
    return crc;
}

size_t bp_encode(uint8_t *buf, size_t cap, uint8_t type, uint8_t seq,
                 const uint8_t *payload, uint8_t len) {
    size_t total = (size_t)len + BP_OVERHEAD;
    if (len > BP_MAX_PAYLOAD || cap < total) return 0;
    buf[0] = BP_SYNC0;
    buf[1] = BP_SYNC1;
    buf[2] = BP_VERSION;
    buf[3] = type;
    buf[4] = seq;
    buf[5] = len;
    for (uint8_t i = 0; i < len; i++) buf[6 + i] = payload[i];
    uint16_t crc = bp_crc16(&buf[2], (size_t)len + 4u);
    buf[6 + len] = (uint8_t)(crc & 0xFFu);
    buf[7 + len] = (uint8_t)(crc >> 8);
    return total;
}

void bp_parser_init(bp_parser_t *p) {
    p->st = 0;
    p->idx = 0;
    p->crc_errors = p->version_errors = p->resyncs = p->frames_ok = 0;
}

/* Parser states: 0 want SYNC0, 1 want SYNC1, 2 ver, 3 type, 4 seq, 5 len,
 * 6 payload, 7 crc_lo, 8 crc_hi */
int bp_parser_feed(bp_parser_t *p, uint8_t byte, bp_frame_t *out) {
    switch (p->st) {
    case 0:
        if (byte == BP_SYNC0) p->st = 1;
        break;
    case 1:
        if (byte == BP_SYNC1) { p->st = 2; }
        else { p->st = (byte == BP_SYNC0) ? 1 : 0; p->resyncs++; }
        break;
    case 2:
        if (byte != BP_VERSION) { p->version_errors++; p->st = 0; break; }
        p->st = 3;
        break;
    case 3:
        p->f.type = byte;
        p->st = 4;
        break;
    case 4:
        p->f.seq = byte;
        p->st = 5;
        break;
    case 5:
        if (byte > BP_MAX_PAYLOAD) { p->resyncs++; p->st = 0; break; }
        p->f.len = byte;
        p->idx = 0;
        p->st = (byte == 0) ? 7 : 6;
        break;
    case 6:
        p->f.payload[p->idx++] = byte;
        if (p->idx >= p->f.len) p->st = 7;
        break;
    case 7:
        p->crc_lo = byte;
        p->st = 8;
        break;
    case 8: {
        /* rebuild crc input: ver,type,seq,len,payload */
        uint8_t tmp[4 + BP_MAX_PAYLOAD];
        tmp[0] = BP_VERSION;
        tmp[1] = p->f.type;
        tmp[2] = p->f.seq;
        tmp[3] = p->f.len;
        for (uint8_t i = 0; i < p->f.len; i++) tmp[4 + i] = p->f.payload[i];
        uint16_t crc = bp_crc16(tmp, 4u + (size_t)p->f.len);
        uint16_t rx = (uint16_t)p->crc_lo | ((uint16_t)byte << 8);
        p->st = 0;
        if (crc == rx) {
            p->frames_ok++;
            *out = p->f;
            return 1;
        }
        p->crc_errors++;
        break;
    }
    default:
        p->st = 0;
        break;
    }
    return 0;
}

void bp_pack_i16(uint8_t *at, int16_t v) {
    at[0] = (uint8_t)((uint16_t)v & 0xFFu);
    at[1] = (uint8_t)((uint16_t)v >> 8);
}
void bp_pack_i32(uint8_t *at, int32_t v) {
    at[0] = (uint8_t)((uint32_t)v & 0xFFu);
    at[1] = (uint8_t)(((uint32_t)v >> 8) & 0xFFu);
    at[2] = (uint8_t)(((uint32_t)v >> 16) & 0xFFu);
    at[3] = (uint8_t)(((uint32_t)v >> 24) & 0xFFu);
}
void bp_pack_u16(uint8_t *at, uint16_t v) {
    at[0] = (uint8_t)(v & 0xFFu);
    at[1] = (uint8_t)(v >> 8);
}
int16_t bp_unpack_i16(const uint8_t *at) {
    return (int16_t)((uint16_t)at[0] | ((uint16_t)at[1] << 8));
}
int32_t bp_unpack_i32(const uint8_t *at) {
    return (int32_t)((uint32_t)at[0] | ((uint32_t)at[1] << 8) |
                     ((uint32_t)at[2] << 16) | ((uint32_t)at[3] << 24));
}
uint16_t bp_unpack_u16(const uint8_t *at) {
    return (uint16_t)((uint16_t)at[0] | ((uint16_t)at[1] << 8));
}

size_t bp_encode_cmd_vel(uint8_t *buf, size_t cap, uint8_t seq,
                         const int16_t vel_mmps[4]) {
    uint8_t pl[8];
    for (int i = 0; i < 4; i++) bp_pack_i16(&pl[2 * i], vel_mmps[i]);
    return bp_encode(buf, cap, BP_T_CMD_VEL, seq, pl, 8);
}

size_t bp_encode_telemetry(uint8_t *buf, size_t cap, uint8_t seq,
                           const bp_telemetry_t *t) {
    uint8_t pl[BP_TELEMETRY_LEN];
    pl[0] = t->state;
    bp_pack_u16(&pl[1], t->fault_bits);
    pl[3] = t->estop;
    pl[4] = t->cmd_seq_echo;
    for (int i = 0; i < 4; i++) bp_pack_i32(&pl[5 + 4 * i], t->wheel_pos[i]);
    for (int i = 0; i < 4; i++) bp_pack_i16(&pl[21 + 2 * i], t->wheel_vel[i]);
    for (int i = 0; i < 4; i++) bp_pack_i16(&pl[29 + 2 * i], t->motor_cur_ma[i]);
    bp_pack_u16(&pl[37], t->vbat_mv);
    return bp_encode(buf, cap, BP_T_TELEMETRY, seq, pl, BP_TELEMETRY_LEN);
}

int bp_decode_telemetry(const bp_frame_t *f, bp_telemetry_t *t) {
    if (f->type != BP_T_TELEMETRY || f->len != BP_TELEMETRY_LEN) return 0;
    const uint8_t *pl = f->payload;
    t->state = pl[0];
    t->fault_bits = bp_unpack_u16(&pl[1]);
    t->estop = pl[3];
    t->cmd_seq_echo = pl[4];
    for (int i = 0; i < 4; i++) t->wheel_pos[i] = bp_unpack_i32(&pl[5 + 4 * i]);
    for (int i = 0; i < 4; i++) t->wheel_vel[i] = bp_unpack_i16(&pl[21 + 2 * i]);
    for (int i = 0; i < 4; i++) t->motor_cur_ma[i] = bp_unpack_i16(&pl[29 + 2 * i]);
    t->vbat_mv = bp_unpack_u16(&pl[37]);
    return 1;
}
