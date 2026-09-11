# Exercise 03 – Network traffic and its effect on QoE

This exercise connects the network layer to the perceived quality of a real-time service. Students capture and analyze a VoIP call, build a packet generator in Scapy to see how audio becomes a stream of RTP packets, use the Linux traffic-control subsystem to impose delay and packet loss on a link, and finally evaluate the resulting speech quality with subjective and objective methods.

> [!IMPORTANT]
> This is a multi-week activity carried out in pairs or groups of three. Save captures, recordings, and results after every session.

## Learning objectives

- Identify the signaling (SIP) and media (RTP) components of a VoIP call in a packet capture and relate them to the TCP/IP layers.
- Explain how a PCM speech signal is packetized into RTP and compute the resulting packet rate and bit rate.
- Craft and send IP, UDP, and RTP packets with Scapy and observe them on the wire.
- Emulate delay, jitter, and random or bursty packet loss with `tc netem`.
- Assess speech quality with the ACR and DCR subjective methods and with the PESQ and ViSQOL objective models, and relate the scores to the measured network impairments and to each other.

## Knowledge prerequisites

Students should be able to:

- Explain sampling and pulse-code modulation from [Exercise 01](../qos-01/README.md), and calculate a bit rate from the sample rate and bits per sample.
- Distinguish Ethernet frames, IP packets, and transport-layer ports, and describe the basic roles of TCP and UDP.
- Explain how queues introduce waiting time and interpret a probability as a fraction of events, using [Exercise 02](../qos-02/README.md).
- Write Python functions and loops, and run terminal commands with file paths and arguments.

Voice-call signaling, audio packetization, traffic-control commands, and speech quality assessment are introduced in this exercise. Packet capture and generation are practiced using Wireshark and Scapy.

## Theory

### Anatomy of a VoIP call

Voice over IP (VoIP) separates signaling from media transport. *Signaling* establishes, modifies, and terminates the session; in this course it is the Session Initiation Protocol (SIP), carried over UDP or TCP, whose messages (`INVITE`, `200 OK`, `ACK`, `BYE`) also negotiate the codec and transport addresses of the media. *Media* is carried by the Real-time Transport Protocol (RTP) over UDP. The basic RTP header is 12 bytes long; optional fields can extend it. It contains a payload type, a sequence number, a timestamp, and a synchronization source identifier (SSRC), followed by a block of coded audio.

With the G.711 codec of [Exercise 01](../qos-01/README.md#pulse-code-modulation), speech is sampled at 8 kHz with 8 bits per sample and packetized every 20 ms. One packet therefore carries 160 samples, that is 160 B of payload; with the 12 B RTP, 8 B UDP, and 20 B IPv4 headers without options it is 200 B long. The call produces 50 packets per second in each direction, a 64 kbit/s payload stream and an 80 kbit/s IP stream:

$$
R_{\mathrm{IP}} = \frac{(160 + 12 + 8 + 20) \cdot 8}{0.02} = 80\,000 \ \mathrm{bit/s}
$$

where the numerator is the packet length in bits and the denominator the packetization interval [s]. The payload type field distinguishes A-law (PCMA, type 8, used in Europe) from μ-law (PCMU, type 0).

### Network impairments

Three network impairments affect the received audio and the ease of conversation. Their perceptual effects also depend on the codec, receiver, and speech content.

- **Delay** – the one-way latency from microphone to loudspeaker, including coding, packetization, queueing, propagation, and playout buffering. The guidance in ITU-T G.114 emphasizes keeping conversational delay low. Large delays disrupt turn-taking; a listening-only test does not measure this conversational effect.
- **Jitter** – the variation of delay between consecutive packets, caused by queueing. The receiver absorbs it in a *jitter buffer*, at the cost of additional delay; packets arriving later than the buffer allows are treated as lost.
- **Packet loss** – packets discarded by congested queues or corrupted on the link. In the 20 ms packetization example, each missing packet removes 20 ms of coded speech. A receiver may replace it using packet-loss concealment. Consecutive losses can remove whole syllables, so *bursty* loss can be more disruptive than independent loss at the same average rate.

### Traffic control in Linux

The `tc` utility configures the kernel packet scheduler. Every interface has a root *queueing discipline* (qdisc) that decides when outgoing packets are transmitted. The `netem` qdisc emulates network impairments on an otherwise ideal link:

```bash
tc qdisc add dev DEVICE root netem delay TIME loss PERCENT%
```

`dev DEVICE` selects the interface, `root netem` installs netem as the root qdisc, `delay TIME` adds a fixed delay to every outgoing packet, and `loss PERCENT%` drops packets independently at random with the given probability. A second delay argument adds variation; specify the distribution explicitly, for example `delay 100ms 20ms distribution normal`. See the [netem manual](https://github.com/iproute2/iproute2/blob/main/man/man8/tc-netem.8).

Bursty loss is emulated with the Gilbert–Elliott model, a two-state Markov chain that alternates between a *good* state with no loss and a *bad* state in which packets are lost:

```bash
tc qdisc add dev DEVICE root netem loss gemodel P R 100% 0%
```

where `P` is the probability of moving from the good to the bad state after a packet and `R` the probability of returning from bad to good, both in percent. The final two parameters specify 100 % loss in the bad state and 0 % in the good state. With `P` and `R` converted to probabilities, the long-run loss fraction is $P/(P+R)$ and the mean bad-state duration is $1/R$ packets. Thus `R` controls the mean burst length; `P` must also change to hold the mean loss fixed.

The current configuration is shown with `tc qdisc show dev DEVICE` and removed with `tc qdisc del dev DEVICE root`; the interface then returns to its default behavior.

> [!WARNING]
> `tc` requires superuser privileges (`sudo`). Apply it only to the second, laboratory interface of the server, never to the interface carrying the SSH session, and delete the qdisc when the measurement is finished.

### Speech quality assessment

Subjective methods collect judgments from listeners. Objective models estimate listening quality from audio signals. Keep the measurement names distinct when reporting results:

| Method | What is assessed | Reported result |
|---|---|---|
| Absolute Category Rating (ACR) | Quality of a sample presented on its own | Mean opinion score (MOS) |
| Degradation Category Rating (DCR) | Degradation of a sample relative to the clean reference played first | Degradation mean opinion score (DMOS) |
| Perceptual Evaluation of Speech Quality (PESQ) | A model's comparison of reference and degraded speech | Raw prediction and, where provided, its mapped listening-quality estimate |
| Virtual Speech Quality Objective Listener (ViSQOL) | A model's comparison of reference and degraded audio | Mean opinion score – listening quality objective (MOS-LQO) |

Use these rating anchors, following [ITU-T P.800](https://www.itu.int/rec/T-REC-P.800-199608-I/en):

| Score | ACR: quality | DCR: degradation |
|---|---|---|
| 5 | Excellent | Inaudible |
| 4 | Good | Audible but not annoying |
| 3 | Fair | Slightly annoying |
| 2 | Poor | Annoying |
| 1 | Bad | Very annoying |

PESQ and ViSQOL are *full-reference* or *intrusive* models: both need the clean reference as well as the degraded recording. ViSQOL compares patterns of energy across time and frequency and maps their similarity to an estimated quality score. Its speech mode expects 16 kHz audio; resampling an 8 kHz recording meets that input requirement but does not recover missing high-frequency content. See the [ViSQOL documentation](https://github.com/google/visqol).

These two models estimate listening quality. This experiment does not measure the effect of conversational delay on turn-taking. Similar numerical ranges also do not make ACR MOS, DCR DMOS, and objective estimates interchangeable; compare their trends and explain their different meanings.

## Exercise

### Preparation

The Scapy notebook needs raw-socket access. Either run the kernel as root, or grant the capability to the interpreter and to `tcpdump` once:

```bash
sudo setcap cap_net_raw=eip /usr/bin/pythonX.X
sudo setcap cap_net_raw=eip /usr/bin/tcpdump
```

Create the environment and start JupyterLab as described in the [root README](../README.md), then open `qos_03/exercise_03.ipynb`.

```bash
cd qos-03
uv sync
uv run jupyter lab --ip 0.0.0.0
```

The audio part of the notebook expects `input.wav` in the notebook directory: mono, 8 kHz, signed 16-bit linear PCM. A recording in any other format is converted with

```bash
ffmpeg -i recording.m4a -ar 8000 -ac 1 -sample_fmt s16 input.wav
```

A sample capture is provided in `qos_03/pcap/asterisk-echo-test.pcapng`. Its outgoing G.711 A-law stream has SSRC `0xabd66334`, source `10.100.100.3:42132`, and destination `158.196.146.236:16088`. It contains 1095 packets with 160 samples each, giving 21.9 s of audio. Use it to check stream selection and reconstruction before processing a new recording.

For the commands in Steps 4–6, work in `qos-03/qos_03/`. Create a `results/` directory there. Keep a separate capture for every condition, and record:

| Parameter | What to record |
|---|---|
| Sender and receiver | IP and Ethernet MAC addresses; laboratory interface names |
| Stream | Source and destination ports, SSRC, codec, and packetization interval |
| Impairment | Complete `tc` command, configured mean loss, and burst parameters |
| Observation | Capture duration, sent and received packet counts, measured loss, and jitter |
| Quality evaluation | Reference file, reconstruction method, listener count, and model version/settings |

Step 1 uses the student's local Wireshark installation and telephone client. Packet generation, replay, reconstruction, and scoring run on the laboratory servers. Use the available PESQ and ViSQOL executables by setting their paths in the notebook. Source-build instructions are provided below as optional setup; a missing executable produces an unavailable score (`NaN`), not a zero quality rating.

### Step 1 – Make a call and capture it

Start a Wireshark capture on the local interface and place a call to the laboratory Asterisk PBX with the SIP credentials distributed through the LMS. Call a colleague's extension or the echo service at extension `*43`. In the capture, identify the SIP dialog and the RTP streams (*Telephony → VoIP Calls* and *Telephony → RTP → RTP Streams*), locate the codec and the payload inside an RTP packet, and map every protocol seen to its layer of the TCP/IP stack.

### Step 2 – Build a traffic generator

Work through the notebook. Scapy composes packets layer by layer (`IP() / ICMP() / "text"`), shows them before and after finalization (`show()`, `show2()`, `hexdump()`), sends them (`send()`), and captures them (`sniff()`). Then complete the notebook tasks: rewrite the text exchange over UDP sending one character per packet, add random inter-packet delays and random losses to the sender, and run `send_audio_as_rtp()` to transmit `input.wav` as G.711 in RTP. Verify each step in Wireshark, and note the timing precision Scapy can achieve from Python.

### Step 3 – Emulate impairments with `tc`

On the laboratory interface, apply fixed delay, delay with jitter, random loss, and Gilbert–Elliott loss in separate trials. Remove the previous root qdisc before adding the next one. Predict the effect, send the same traffic in each trial, and inspect the receiver capture. Use sequence numbers to measure loss and packet timing to examine jitter. Measuring absolute one-way delay requires corresponding sender and receiver observations with synchronized clocks; a receiver-only capture is insufficient.

### Step 4 – Replay a call under packet loss

Prepare `rtp.pcap` containing one direction of one G.711 stream with 20 ms packetization and no missing packets. For the supplied example, export the outgoing stream:

```bash
tshark -nr pcap/asterisk-echo-test.pcapng -Y "rtp.ssrc == 0xabd66334" -F pcap -w rtp.pcap
```

Replay a clean baseline first, then apply 0.5 %, 1 %, and 3 % independent loss in separate trials. Start the receiver capture before replay and stop it after replay finishes. Use `tcpreplay-edit` on the sender, substituting the original capture addresses for `OLD_SRC_IP` and `OLD_DST_IP`, and the laboratory addresses for the other placeholders:

```bash
sudo tcpreplay-edit -i DEVICE -K --loop 1 --timer nano --pps 50 --dlt=enet --fixcsum \
  --srcipmap=OLD_SRC_IP/32:SRC_IP --dstipmap=OLD_DST_IP/32:DST_IP \
  --enet-smac=SRC_MAC --enet-dmac=DST_MAC rtp.pcap
```

`-K` preloads the capture, `--pps 50` requests 50 packets/s, and the map options rewrite the addresses. The supplied capture uses Linux cooked headers; `--dlt=enet` converts them to Ethernet headers, and `--fixcsum` recalculates checksums. See the [tcpreplay-edit manual](https://tcpreplay.appneta.com/reference/man/tcpreplay-edit/). This rate applies to the selected single stream; replaying two directions at 50 packets/s would change their timing. For the supplied stream, the original addresses are `10.100.100.3` and `158.196.146.236`.

Check qdisc counters and receiver statistics to establish that the replay passed through the intended impairment. Record observed loss rather than assuming it equals the configured probability. Repeat with bursty loss at comparable mean rates, recording all Gilbert–Elliott parameters. Retain the received captures for reconstruction and comparison.

### Step 5 – Reconstruct and evaluate the audio

Reconstruct the source timeline before evaluating quality. Simply joining the received payloads would remove missing intervals and shorten the recording. RTP timestamps locate audio samples on the source timeline, and sequence numbers help identify missing or repeated packets. See [RFC 3550, Section 2.1](https://www.rfc-editor.org/rfc/rfc3550.html#section-2.1).

For example, if packets at timestamps 0, 160, and 320 carry 160 samples each, losing the middle packet should leave a 160-sample gap. At 8 kHz, that gap is 20 ms; the recording should still last 60 ms.

The supplied [reconstruction utility](reconstruct_rtp.py) decodes G.711, puts received samples at their original offsets, and inserts digital silence for missing packets, including losses at the beginning or end. It uses the complete clean stream to establish the duration. This is an offline loss model: it accepts reordered packets and does not simulate late-packet rejection or a receiver's jitter buffer. Silence insertion is a baseline, not a model of every real receiver's concealment algorithm.

Export the clean stream and one received stream as tab-separated sequence number, timestamp, and payload fields. Replace `PORT` and `SSRC` with the recorded destination port and stream identifier; replay preserves the SSRC. Select the same direction in both files:

```bash
tshark -nr rtp.pcap -d udp.port==PORT,rtp -Y "rtp.ssrc == SSRC" \
  -T fields -e rtp.seq -e rtp.timestamp -e rtp.payload > results/reference.tsv
tshark -nr received.pcap -d udp.port==PORT,rtp -Y "rtp.ssrc == SSRC" \
  -T fields -e rtp.seq -e rtp.timestamp -e rtp.payload > results/received.tsv
```

For the supplied example, use `PORT=16088` and `SSRC=0xabd66334` as the placeholder values. The utility expects continuous G.711 audio from one stream, without silence suppression or codec changes. It rejects an incomplete clean timeline. Decode the clean and received exports with the same settings:

```bash
python3 ../reconstruct_rtp.py results/reference.tsv results/reference.tsv results/reference.wav --codec alaw
python3 ../reconstruct_rtp.py results/reference.tsv results/received.tsv results/output_random_0.5.wav --codec alaw
```

Use `--codec mulaw` for PCMU. Name each output `output_<model>_<loss>.wav`, using `random` or `gemodel` and the configured mean loss percentage, so the notebook can find it. Keep repeated trials in separate result directories. Verify that every reconstructed recording has the same duration as the reference and that a capture with no loss reproduces its decoded samples.

For listening tests, use consistent headphones, playback level, and a quiet setting. Assign anonymous sample labels and randomize the order of conditions. Collect ACR ratings separately from DCR ratings; for DCR, always play the reference before the degraded version. Retain individual ratings and report their mean, spread, and listener count. A small classroom group illustrates the method but does not establish a population-wide quality ranking.

Set `PESQ_BIN` in the notebook and use its *Quality evaluation* section to score the files. Label the mapped PESQ score as MOS-LQO where available, and identify raw predictions separately. Tabulate configured and observed loss, jitter, ACR MOS, DCR DMOS, and objective estimates.

### Step 6 – Score with ViSQOL

Set `VISQOL_BIN` to the available executable and run the notebook's scoring cells. The helper resamples both files to 16 kHz and invokes speech mode. It uses `--use_unscaled_speech_mos_mapping`; record this option with the tool version because score mapping affects comparisons.

The notebook combines these estimates with hand-entered network statistics and listener ratings. Treat `NaN` as an unavailable result and check executable paths if a score is missing. Compare how the methods rank the conditions and where their trends disagree. Do not infer a universal ordering of PESQ and ViSQOL from one recording or a small listener group.

### Optional setup – Build the scoring tools

If source builds are needed, prepare them separately from the measurements. For PESQ, use the reference C sources linked in References and run this command in their directory:

```bash
gcc -o PESQ *.c -lm -fcommon
```

For ViSQOL, follow the dependencies and version requirements in its [build documentation](https://github.com/google/visqol#build). From a chosen tools directory:

```bash
git clone https://github.com/google/visqol.git
cd visqol
bazel build :visqol -c opt
```

Record the source revision and set the absolute executable paths in the notebook. Build steps do not need to be repeated for each measurement.

### Results to retain

Save the completed notebook, clean and received captures, reconstructed WAV files, full impairment settings, and individual listener ratings. Include the comparison table and plots, a successful no-loss reconstruction check, and a short discussion of loss patterns, measurement variation, and disagreements between quality methods. Retain these artifacts as work progresses; groups may complete the steps at different rates.

## Questions

1. Which layer of the TCP/IP stack does each of SIP, RTP, UDP, and IP belong to, and which of them carries the codec information?
2. What is the IP-level bit rate of a G.711 call in both directions, and how does it change if the packetization interval is 40 ms?
3. How closely did the observed packet spacing match 20 ms? Which software and operating-system effects can introduce timing variation?
4. Two links have the same 3 % average loss, one independent and one bursty. Predict how speech quality might differ, then explain how speech content and packet-loss concealment could affect the result.
5. Which of your measurements would change between a listening test and a conversational test, and why do PESQ and ViSQOL ignore it?
6. PESQ and ViSQOL are both intrusive models. What does a *non-intrusive* model have to do differently, and where in a VoIP system would it be needed?

## References

1. H. Schulzrinne, S. Casner, R. Frederick, and V. Jacobson, "RTP: A Transport Protocol for Real-Time Applications," RFC 3550, 2003.
2. J. Rosenberg et al., "SIP: Session Initiation Protocol," RFC 3261, 2002.
3. ITU-T Recommendation G.711, *Pulse code modulation (PCM) of voice frequencies*, 1988.
4. ITU-T Recommendation G.114, *One-way transmission time*, 2003.
5. ITU-T Recommendation P.800, *Methods for subjective determination of transmission quality*, 1996.
6. ITU-T Recommendation P.862, *Perceptual evaluation of speech quality (PESQ)*, 2001. Reference sources: https://drive.google.com/file/d/15UCvcW7bdYVAVa3g9aXji06x0WfAOdYE/view?usp=sharing (requires GCC 9 or newer with `-fcommon`).
7. M. Chinen, F. S. C. Lim, J. Skoglund, N. Gureev, F. O'Gorman, and A. Hines, "ViSQOL v3: An Open Source Production Ready Objective Speech and Audio Metric," in *Proc. 12th Int. Conf. on Quality of Multimedia Experience (QoMEX)*, 2020. Source: https://github.com/google/visqol.
8. Scapy documentation, https://scapy.readthedocs.io/.
9. `tc-netem(8)` manual page; tcpreplay documentation, https://tcpreplay.appneta.com/.
