"""Unit tests for buddy_protocol.py, incl. cross-implementation golden vectors.

Run:  python3 test_protocol.py
The golden vector byte strings are the exact output of the C implementation
(firmware/shared_protocol/tests/test_protocol.c prints them) — if either
implementation drifts, these fail.
"""

import unittest

import buddy_protocol as bp


class TestCrc(unittest.TestCase):
    def test_check_value(self):
        self.assertEqual(bp.crc16(b"123456789"), 0x29B1)


class TestGoldenVectors(unittest.TestCase):
    """Byte-identical with the C implementation."""

    def test_ping(self):
        self.assertEqual(bp.encode(bp.T_PING, 7).hex(), "b5dd01030700b332")

    def test_cmd_vel(self):
        frame = bp.encode_cmd_vel(1, (100, -100, 250, -250))
        self.assertEqual(frame.hex(), "b5dd0101010864009cfffa0006fff247")


class TestRoundTrip(unittest.TestCase):
    def test_cmd_vel_roundtrip(self):
        p = bp.Parser()
        frames = p.feed(bp.encode_cmd_vel(3, (750, -750, 0, 1)))
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].type, bp.T_CMD_VEL)
        self.assertEqual(frames[0].seq, 3)

    def test_telemetry_roundtrip(self):
        t = bp.Telemetry(state=bp.STATE_ACTIVE, fault_bits=bp.FAULT_CMD_TIMEOUT,
                         estop=0, cmd_seq_echo=42,
                         wheel_pos=(123456, -123456, 1, -1),
                         wheel_vel=(750, -750, 100, -100),
                         motor_cur_ma=(8000, -8000, 500, 0), vbat_mv=11100)
        p = bp.Parser()
        frames = p.feed(bp.encode_telemetry(9, t))
        self.assertEqual(len(frames), 1)
        r = bp.Telemetry.unpack(frames[0].payload)
        self.assertEqual(r, t)

    def test_byte_at_a_time(self):
        p = bp.Parser()
        data = bp.encode_cmd_vel(1, (1, 2, 3, 4))
        got = []
        for i in range(len(data)):
            got += p.feed(data[i:i + 1])
        self.assertEqual(len(got), 1)

    def test_corrupt_rejected_then_resync(self):
        p = bp.Parser()
        good = bp.encode_cmd_vel(1, (100, -100, 250, -250))
        bad = bytearray(good)
        bad[10] ^= 0xFF
        frames = p.feed(bytes(bad) + good)
        self.assertEqual(len(frames), 1)
        self.assertEqual(p.crc_errors, 1)

    def test_garbage_prefix(self):
        p = bp.Parser()
        frames = p.feed(b"\x00\xb5\x11\xff" + bp.encode(bp.T_PING, 0))
        self.assertEqual(len(frames), 1)
        self.assertGreaterEqual(p.resyncs, 1)

    def test_wrong_version_dropped(self):
        p = bp.Parser()
        frame = bytearray(bp.encode(bp.T_PING, 0))
        frame[2] = 0x02  # wrong version
        self.assertEqual(p.feed(bytes(frame)), [])
        self.assertEqual(p.version_errors, 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
