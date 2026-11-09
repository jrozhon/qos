"""Checks for the G.711 codec, the RTP builders, the loss models, and the capture
analysis."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import scapy.all as sa

# The notebook imports "lib.*" with qos_03/ as the working directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "qos_03"))

from lib.capture import (  # noqa: E402
    compare_streams,
    decode_rtp,
    list_streams,
    rfc3550_jitter,
    rtp_stream,
    sdp_view,
    skip_loopback_copies,
    stream_stats,
    stream_summary,
)
from lib.core import (  # noqa: E402
    G711,
    MarkovChain,
    gilbert_elliott,
    gilbert_elliott_dict,
    gilbert_elliott_params,
    loss_bursts,
    netem_state_dict,
    netem_state_loss,
    rtp_header,
    rtp_packets,
)
from lib.packetviz import finalize, find_silences, packet_fields  # noqa: E402

PCAP = (
    Path(__file__).resolve().parents[1]
    / "qos_03"
    / "pcap"
    / "asterisk-echo-test.pcapng"
)
FFMPEG_FORMAT = {"alaw": "alaw", "ulaw": "mulaw"}


def ffmpeg(data: bytes, src: str, dst: str) -> bytes:
    """Convert raw 8 kHz mono audio between two FFmpeg raw formats."""
    return subprocess.run(
        ["ffmpeg", "-v", "error", "-f", src, "-ar", "8000", "-ac", "1", "-i", "pipe:0"]
        + ["-f", dst, "pipe:1"],
        input=data,
        capture_output=True,
        check=True,
    ).stdout


class CodecTests(unittest.TestCase):
    def test_decode_then_encode_returns_every_code(self):
        codes = np.arange(256, dtype=np.uint8)
        for name, (_, encode, decode) in G711.items():
            with self.subTest(codec=name):
                again = encode(decode(codes))
                # μ-law has two codes for zero (0x7F and 0xFF); 0 encodes as 0xFF.
                differ = codes[again != codes]
                self.assertTrue(set(differ) <= ({0x7F} if name == "ulaw" else set()))

    def test_full_scale_values_do_not_overflow(self):
        x = np.array([-32768, -32767, 32767, 0], dtype=np.int16)
        for name, (_, encode, decode) in G711.items():
            with self.subTest(codec=name):
                y = decode(encode(x)).astype(int)
                self.assertTrue(np.all(np.sign(y[:3]) == np.sign(x[:3])))
                self.assertLess(np.max(np.abs(y[:3] - x[:3].astype(int))), 1100)

    def test_snr_of_speech_level_sine_is_near_38_db(self):
        n = np.arange(8000)
        x = np.round(8000 * np.sin(2 * np.pi * 1019 / 8000 * n)).astype(np.int16)
        for name, (_, encode, decode) in G711.items():
            with self.subTest(codec=name):
                e = x.astype(float) - decode(encode(x))
                snr = 10 * np.log10(np.sum(x.astype(float) ** 2) / np.sum(e**2))
                self.assertGreater(snr, 35)

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is required")
    def test_decoder_matches_ffmpeg(self):
        codes = np.arange(256, dtype=np.uint8)
        for name, (_, _, decode) in G711.items():
            with self.subTest(codec=name):
                reference = np.frombuffer(
                    ffmpeg(codes.tobytes(), FFMPEG_FORMAT[name], "s16le"), np.int16
                )
                np.testing.assert_array_equal(decode(codes), reference)

    def test_every_input_lies_within_half_a_step_of_its_level(self):
        # G.711 defines decision intervals; the decoder returns their middle.
        x = np.arange(-32000, 32001, dtype=np.int16)
        for name, (_, encode, decode) in G711.items():
            with self.subTest(codec=name):
                codes = encode(x)
                plain = codes ^ 0x55 if name == "alaw" else ~codes
                segment = (plain.astype(int) & 0x70) >> 4
                if name == "alaw":  # step 32 in segments 0 and 1, then doubling
                    half_step = 16 << np.maximum(segment - 1, 0)
                else:  # step 8 in segment 0, then doubling, after the input
                    # is truncated to 14 bits (up to 3 more for negatives)
                    half_step = (4 << segment) + 3
                error = np.abs(x.astype(int) - decode(codes))
                self.assertTrue(np.all(error <= half_step))

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is required")
    def test_encoder_agrees_with_ffmpeg_away_from_segment_edges(self):
        x = np.arange(-32768, 32768, dtype=np.int16)
        for name, (_, encode, _) in G711.items():
            with self.subTest(codec=name):
                theirs = np.frombuffer(
                    ffmpeg(x.tobytes(), "s16le", FFMPEG_FORMAT[name]), np.uint8
                )
                # FFmpeg picks the nearest level, which differs from the G.711
                # decision intervals only next to segment boundaries.
                self.assertLess(np.mean(encode(x) != theirs), 0.02)


class RtpTests(unittest.TestCase):
    def test_header_matches_scapy(self):
        for seq, ts, ssrc, pt, marker in [
            (0, 0, 0x12345678, 8, 1),
            (65535, 2**32 - 160, 0xDEADBEEF, 0, 0),
        ]:
            scapy_header = bytes(
                sa.RTP(
                    marker=marker,
                    payload_type=pt,
                    sequence=seq,
                    timestamp=ts,
                    sourcesync=ssrc,
                )
            )
            self.assertEqual(rtp_header(seq, ts, ssrc, pt, marker), scapy_header)

    def test_packets_count_samples_and_wrap(self):
        samples = np.zeros(160 * 4 + 10, dtype=np.int16)
        packets = rtp_packets(
            samples,
            "10.0.0.2",
            5000,
            4000,
            first_sequence=65534,
            first_timestamp=2**32 - 160,
        )
        self.assertEqual(len(packets), 5)
        self.assertEqual([p[sa.RTP].sequence for p in packets], [65534, 65535, 0, 1, 2])
        self.assertEqual(
            [p[sa.RTP].timestamp for p in packets], [2**32 - 160, 0, 160, 320, 480]
        )
        self.assertEqual([p[sa.RTP].marker for p in packets], [1, 0, 0, 0, 0])
        self.assertTrue(all(len(p[sa.Raw].load) == 160 for p in packets))
        self.assertEqual(len(finalize(packets[0])), 200)

    def test_field_map_covers_every_bit(self):
        packet = rtp_packets(np.zeros(160, dtype=np.int16), "10.0.0.2", 5000, 4000)[0]
        fields = packet_fields(packet)
        self.assertEqual(sum(f["bits"] for f in fields), 8 * 200)
        rtp = [f["name"] for f in fields if f["layer"] == "RTP"]
        self.assertEqual(
            rtp[:6],
            ["version", "padding", "extension", "numsync", "marker", "payload_type"],
        )


class SilenceTests(unittest.TestCase):
    def test_pauses_are_found_and_short_gaps_skipped(self):
        rng = np.random.default_rng(0)
        t = np.arange(4 * 8000) / 8000
        samples = 8000 * np.sin(2 * np.pi * 200 * t)
        samples[8000:12000] = rng.normal(0, 30, 4000)  # 500 ms pause with noise
        samples[20000:20800] = 0  # 100 ms digital silence
        samples[28000:28400] = rng.normal(0, 30, 400)  # 50 ms, too short
        found = find_silences(samples.astype(np.int16))
        self.assertEqual(found["start"].tolist(), [8000, 20000])
        self.assertEqual(found["duration"].tolist(), [500.0, 100.0])
        self.assertTrue(np.isfinite(found["level"].iloc[0]))
        self.assertEqual(found["level"].iloc[1], -np.inf)


class MarkovTests(unittest.TestCase):
    def test_chain_follows_the_state_dictionary(self):
        chain = MarkovChain(
            {"a": (["a", "b"], [0.5, 0.5]), "b": (["c"], [1.0]), "c": (["a"], [1.0])},
            "c",
            np.random.default_rng(1),
        )
        states = chain.run(200)
        self.assertEqual(chain.check_state(display=False), states[-1])
        allowed = {("a", "a"), ("a", "b"), ("b", "c"), ("c", "a")}
        pairs = set(zip(["c", *states[:-1]], states))
        self.assertTrue(pairs <= allowed)

    def test_lecture_notebook_format_is_accepted(self):
        # Two-row arrays: NumPy turns the probabilities into strings
        state_dict = {
            "1": np.array([["1", "3", "4"], [0.98, 0.02, 0.0]]),
            "2": np.array([["2", "3"], [1.0, 0.0]]),
            "3": np.array([["1", "2", "3"], [0.3, 0.0, 0.7]]),
            "4": np.array([["1"], [1.0]]),
        }
        chain = MarkovChain(state_dict, "1")
        self.assertIn(chain.next_state(), {"1", "3"})
        pi = chain.stationary_distribution()
        self.assertAlmostEqual(pi["3"], 0.02 / 0.32)
        self.assertEqual(pi["2"], 0.0)  # unreachable from state 1

    def test_invalid_probabilities_are_refused(self):
        with self.assertRaises(ValueError):
            MarkovChain({"a": (["a", "b"], [0.5, 0.4]), "b": (["a"], [1.0])}, "a")

    def test_stationary_distribution_of_gilbert_elliott(self):
        p, r = 0.02, 0.3
        pi = MarkovChain(gilbert_elliott_dict(p, r), "good").stationary_distribution()
        self.assertAlmostEqual(pi["good"], r / (p + r))
        self.assertAlmostEqual(pi["bad"], p / (p + r))

    def test_four_state_model_reduces_to_gilbert_elliott(self):
        p, r = gilbert_elliott_params(loss=0.05, burst=4)
        lost = netem_state_loss(200_000, p, r, rng=np.random.default_rng(4))
        self.assertAlmostEqual(lost.mean(), 0.05, delta=0.005)
        self.assertAlmostEqual(loss_bursts(lost).mean(), 4, delta=0.2)
        pi = MarkovChain(
            netem_state_dict(0.01, 0.3, 0.2, 0.4, 0.01), "1"
        ).stationary_distribution()
        self.assertAlmostEqual(sum(pi.values()), 1)
        self.assertTrue(all(v > 0 for v in pi.values()))

    def test_params_give_mean_loss_and_burst(self):
        p, r = gilbert_elliott_params(loss=0.03, burst=3)
        self.assertAlmostEqual(r, 1 / 3)
        self.assertAlmostEqual(p / (p + r), 0.03)

    def test_simulated_loss_and_bursts_match_the_model(self):
        p, r = gilbert_elliott_params(loss=0.05, burst=4)
        lost = gilbert_elliott(200_000, p, r, np.random.default_rng(2))
        self.assertAlmostEqual(lost.mean(), 0.05, delta=0.005)
        self.assertAlmostEqual(loss_bursts(lost).mean(), 4, delta=0.2)

    def test_loss_in_good_state_and_partial_loss_in_bad_state(self):
        lost = gilbert_elliott(
            200_000, 0.1, 0.4, np.random.default_rng(3), loss_bad=0.5, loss_good=0.01
        )
        self.assertAlmostEqual(lost.mean(), 0.8 * 0.01 + 0.2 * 0.5, delta=0.005)

    def test_bursts_of_a_pattern(self):
        self.assertEqual(loss_bursts([1, 1, 0, 1, 0, 0, 1, 1, 1]).tolist(), [2, 1, 3])
        self.assertEqual(loss_bursts([0, 0, 0]).size, 0)


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def received(self, keep, order=None, jitter=None):
        """Write a capture of 50 packets of which only `keep` arrive."""
        packets = rtp_packets(
            np.zeros(160 * 50, dtype=np.int16),
            "10.0.0.2",
            5000,
            4000,
            first_sequence=65520,
        )
        out = []
        for i in keep:
            p = packets[i].copy()
            p.time = 100 + 0.02 * i + (0 if jitter is None else jitter[i])
            out.append(p)
        if order is not None:
            out = [out[i] for i in order]
        path = Path(self.temp.name) / "rx.pcap"
        sa.wrpcap(str(path), out)
        return rtp_stream(path, dport=5000)

    def test_losses_and_bursts_across_the_wrap(self):
        lost = {0, 10, 11, 12, 30, 49}
        stream = self.received([i for i in range(50) if i not in lost])
        stats = stream_stats(stream, expected=50, first_sequence=65520)
        self.assertEqual(stats["lost"], 6)
        self.assertAlmostEqual(stats["loss"], 12.0)
        self.assertEqual(sorted(stats["bursts"].tolist()), [1, 1, 1, 3])
        self.assertEqual(stats["reordered"], 0)

    def test_without_expected_count_end_losses_are_missed(self):
        stream = self.received(range(1, 49))
        self.assertEqual(stream_stats(stream)["lost"], 0)

    def test_reordering_is_counted_and_decoded_in_place(self):
        jitter = np.zeros(50)
        jitter[20] = 0.03  # packet 20 arrives after 21
        stream = self.received(range(50), jitter=jitter)
        stream = stream.sort_values("time").reset_index(drop=True)
        self.assertEqual(stream_stats(stream)["reordered"], 1)
        self.assertEqual(len(decode_rtp(stream)), 160 * 50)

    def test_decoded_gap_is_silent_and_keeps_duration(self):
        stream = self.received([i for i in range(50) if i != 5])
        audio = decode_rtp(stream)
        self.assertEqual(len(audio), 160 * 50)
        self.assertTrue(np.all(audio[5 * 160 : 6 * 160] == 0))

    def test_loopback_copies_are_skipped_but_later_repeats_kept(self):
        packets = []
        for t in (0.0, 0.000004, 0.02, 0.020003, 0.5):  # pairs as seen on lo
            p = sa.IP(dst="127.0.0.1") / sa.UDP(dport=5000) / b"same payload"
            p.time = t
            packets.append(p)
        keep = skip_loopback_copies()
        self.assertEqual([keep(p) for p in packets], [True, False, True, False, True])

    def test_jitter_of_perfect_stream_is_zero(self):
        t = np.arange(100) * 0.02
        np.testing.assert_allclose(
            rfc3550_jitter(t, np.arange(100) * 160), 0, atol=1e-9
        )

    def test_jitter_matches_wireshark_on_sample_capture(self):
        stats = stream_stats(rtp_stream(PCAP, ssrc=0xABD66334))
        self.assertEqual(stats["received"], 1095)
        self.assertEqual(stats["lost"], 0)
        # tshark -z rtp,streams: mean jitter 2.721 ms, max 3.098 ms
        self.assertAlmostEqual(stats["jitter"][1:].mean(), 2.721, places=3)
        self.assertAlmostEqual(stats["jitter"].max(), 3.098, places=3)


class RecordedCallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packets = sa.rdpcap(str(PCAP))

    def test_streams_of_the_sample_call(self):
        streams = list_streams(self.packets)
        self.assertEqual(streams["ssrc_hex"].tolist(), ["0xabd66334", "0x28ebdb68"])
        self.assertEqual(streams["packets"].tolist(), [1095, 1090])

    def test_summary_shows_marking_and_timestamp_jump(self):
        pbx = stream_summary(rtp_stream(self.packets, ssrc=0x28EBDB68))
        self.assertEqual(pbx["DSCP"], "46 (EF)")
        self.assertEqual(pbx["TTL"], "60")
        self.assertIn("largest 1781702443", pbx["Timestamp step"])
        phone = stream_summary(rtp_stream(self.packets, ssrc=0xABD66334))
        self.assertEqual((phone["First sequence number"], phone["DSCP"]), ("0", "0"))

    def test_sdp_offer_is_reassembled_and_names_static_types(self):
        text = " ".join(card.object for card in sdp_view(self.packets))
        self.assertIn("8 PCMA/8000 (static)", text)  # offer, no rtpmap line
        self.assertIn("100 telephone-event/8000", text)  # in the second IP fragment
        self.assertIn("ptime:20", text)  # answer

    def test_timestamp_jump_is_refused_by_the_decoder(self):
        with self.assertRaises(ValueError):
            decode_rtp(rtp_stream(self.packets, ssrc=0x28EBDB68))

    def test_comparison_builds(self):
        a = rtp_stream(self.packets, ssrc=0xABD66334)
        b = rtp_stream(self.packets, ssrc=0x28EBDB68)
        self.assertEqual(len(compare_streams({"a": a, "b": b})), 3)


if __name__ == "__main__":
    unittest.main()
