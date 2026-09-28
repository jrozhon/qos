/* G.729 Annex A encode + decode round trip with bcg729, for scripts/generate-codec-samples.py.
 *
 * Reads raw 16-bit mono PCM at 8 kHz on stdin, writes the decoded signal in the same format on stdout.
 * Usage: g729-roundtrip [vad | vad-nocng]
 *   vad        enables Annex B: VAD, DTX and comfort-noise generation (CNG)
 *   vad-nocng  same bitstream, but frames the VAD drops are played as digital silence instead of comfort
 *              noise, so the gating that CNG normally hides becomes audible (a teaching illustration)
 * Build: cc -O2 -o g729-roundtrip g729-roundtrip.c -lbcg729
 */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <bcg729/decoder.h>
#include <bcg729/encoder.h>

int main(int argc, char **argv)
{
    uint8_t vad = argc > 1 && strncmp(argv[1], "vad", 3) == 0;
    uint8_t mute_cng = argc > 1 && strcmp(argv[1], "vad-nocng") == 0;
    bcg729EncoderChannelContextStruct *enc = initBcg729EncoderChannel(vad);
    bcg729DecoderChannelContextStruct *dec = initBcg729DecoderChannel();
    int16_t in[80], out[80];
    uint8_t bits[10], len;
    size_t n;

    while ((n = fread(in, sizeof(int16_t), 80, stdin)) > 0) {
        if (n < 80)
            memset(in + n, 0, (80 - n) * sizeof(int16_t));
        bcg729Encoder(enc, in, bits, &len);
        /* len 10: speech frame, 2: SID (comfort-noise update), 0: untransmitted DTX frame */
        if (len == 0)
            bcg729Decoder(dec, NULL, 0, 1, 1, 0, out);
        else
            bcg729Decoder(dec, bits, len, 0, len == 2, 0, out);
        if (mute_cng && len != 10)
            memset(out, 0, sizeof out);
        fwrite(out, sizeof(int16_t), 80, stdout);
    }
    closeBcg729EncoderChannel(enc);
    closeBcg729DecoderChannel(dec);
    return 0;
}
