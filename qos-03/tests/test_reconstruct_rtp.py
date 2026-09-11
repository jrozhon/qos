"""Checks for timeline preservation in the teaching reconstruction utility."""

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "reconstruct_rtp.py"
spec = importlib.util.spec_from_file_location("reconstruct_rtp", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is required")
class ReconstructionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # Both the sequence number and the timestamp wrap within this stream.
        self.rows = [
            f"{(65534 + i) % 65536}\t{(2**32 - 160 + i * 160) % 2**32}\t"
            + bytes([32 + i] * 160).hex()
            for i in range(5)
        ]
        self.reference = self.write("reference.tsv", self.rows)

    def write(self, name, rows):
        path = self.root / name
        path.write_text("\n".join(rows) + ("\n" if rows else ""))
        return path

    def audio(self, rows, codec="alaw"):
        received = self.write("received.tsv", rows)
        output = self.root / "output.wav"
        module.reconstruct(self.reference, received, output, codec)
        with wave.open(str(output)) as stream:
            self.assertEqual(stream.getframerate(), 8000)
            self.assertEqual(stream.getnchannels(), 1)
            self.assertEqual(stream.getsampwidth(), 2)
            self.assertEqual(stream.getnframes(), 800)
            return stream.readframes(stream.getnframes())

    def test_no_loss_matches_direct_decoding_for_both_codecs(self):
        payload = b"".join(bytes([32 + i] * 160) for i in range(5))
        for codec in ("alaw", "mulaw"):
            with self.subTest(codec=codec):
                expected = subprocess.run(
                    [
                        "ffmpeg",
                        "-v",
                        "error",
                        "-f",
                        codec,
                        "-ar",
                        "8000",
                        "-ac",
                        "1",
                        "-i",
                        "pipe:0",
                        "-f",
                        "s16le",
                        "pipe:1",
                    ],
                    input=payload,
                    capture_output=True,
                    check=True,
                ).stdout
                self.assertEqual(self.audio(self.rows, codec), expected)

    def test_loss_at_start_middle_and_end_preserves_samples(self):
        clean = self.audio(self.rows)
        degraded = self.audio([self.rows[1], self.rows[3]])
        for i in range(5):
            span = slice(i * 320, (i + 1) * 320)
            expected = clean[span] if i in (1, 3) else bytes(320)
            self.assertEqual(degraded[span], expected)

    def test_reordering_and_duplicates(self):
        clean = self.audio(self.rows)
        self.assertEqual(self.audio(self.rows[::-1] + [self.rows[2]]), clean)

    def test_all_packets_lost(self):
        self.assertEqual(self.audio([]), bytes(1600))

    def test_incomplete_reference_is_rejected(self):
        self.reference = self.write("reference.tsv", self.rows[:2] + self.rows[3:])
        with self.assertRaisesRegex(ValueError, "contiguous"):
            self.audio(self.rows)

    def test_wrong_stream_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            self.audio(["9\t42\t" + "aa" * 160])


if __name__ == "__main__":
    unittest.main()
