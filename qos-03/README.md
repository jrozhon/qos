# Lab 03 – Network traffic and its effect on QoE

This lab connects the network layer to the perceived quality of a real-time service. Students capture and analyze a VoIP call, build a packet generator in Scapy to see how audio becomes a stream of RTP packets, use the Linux traffic-control subsystem to impose delay and packet loss on a link, and finally evaluate the resulting speech quality with subjective and objective methods.

> [!IMPORTANT]
> This is a multi-week activity carried out in pairs or groups of three. Save captures, recordings, and results after every session.

## Learning objectives

- Identify the signaling (SIP) and media (RTP) components of a VoIP call in a packet capture and relate them to the TCP/IP layers.
- Explain how a PCM speech signal is companded with G.711 and packetized into RTP, and compute the resulting packet rate and bit rate.
- Build an RTP header field by field, craft and send IP, UDP, and RTP packets with Scapy, observe them on the wire, and compare them with the RTP stream of a real call.
- Emulate delay, jitter, and random or bursty packet loss with `tc netem`, and measure packet loss, loss-burst lengths, and interarrival jitter from a capture.
- Assess speech quality with the ACR and DCR subjective methods and with the PESQ and ViSQOL objective models, and relate the scores to the measured network impairments and to each other.

## Knowledge prerequisites

Students should be able to:

- Explain sampling and pulse-code modulation from [Lab 01](../qos-01/README.md), and calculate a bit rate from the sample rate and bits per sample.
- Distinguish Ethernet frames, IP packets, and transport-layer ports, and describe the basic roles of TCP and UDP.
- Explain how queues introduce waiting time and interpret a probability as a fraction of events, using [Lab 02](../qos-02/README.md).
- Write Python functions and loops, and run terminal commands with file paths and arguments.

Voice-call signaling, audio packetization, traffic-control commands, and speech quality assessment are introduced in this lab. Packet capture and generation are practiced using Wireshark and Scapy.

## Theory

### Anatomy of a VoIP call

Voice over IP (VoIP) separates signaling from media transport. *Signaling* establishes, modifies, and terminates the session; in this course it is the Session Initiation Protocol (SIP), carried over UDP or TCP, whose messages (`INVITE`, `200 OK`, `ACK`, `BYE`) also negotiate the codec and transport addresses of the media. *Media* is carried by the Real-time Transport Protocol (RTP) over UDP. The basic RTP header is 12 bytes long; optional fields can extend it. It contains a payload type, a sequence number, a timestamp, and a synchronization source identifier (SSRC), followed by a block of coded audio.

With the G.711 codec of [Lab 01](../qos-01/README.md#pulse-code-modulation), speech is sampled at 8 kHz with 8 bits per sample and packetized every 20 ms. One packet therefore carries 160 samples, that is 160 B of payload; with the 12 B RTP, 8 B UDP, and 20 B IPv4 headers without options it is 200 B long. The call produces 50 packets per second in each direction, a 64 kbit/s payload stream and an 80 kbit/s IP stream:

$$
R_{\mathrm{IP}} = \frac{(160 + 12 + 8 + 20) \cdot 8}{0.02} = 80\ 000\ \mathrm{bit/s}
$$

where the numerator is the packet length in bits and the denominator the packetization interval [s]. The payload type field distinguishes A-law (PCMA, type 8, used in Europe) from μ-law (PCMU, type 0).

The same calculation holds for any codec. A codec with bit rate $R_c$ fills a payload of $R_c \cdot T / 8$ bytes every packetization interval $T$, and the 40 B of IPv4, UDP, and RTP headers are added to every packet:

$$
R_{\mathrm{IP}} = \frac{(L + 40) \cdot 8}{T}, \qquad L = \frac{R_c \cdot T}{8}
$$

where $R_{\mathrm{IP}}$ is the bit rate of one direction at the IP layer [bit/s], $L$ the payload per packet [B], $T$ the packetization interval [s], and $R_c$ the codec bit rate [bit/s]. Because the headers do not shrink with the payload, a low-rate codec spends most of its IP bit rate on headers:

| Codec | Codec bit rate [kbit/s] | Payload per ms of speech [B] | Payload at 20 ms [B] | IP bit rate at 20 ms [kbit/s] |
|---|---|---|---|---|
| G.711 | 64 | 8 | 160 | 80 |
| G.726-32 | 32 | 4 | 80 | 48 |
| G.729 | 8 | 1 | 20 | 24 |

A capture tool shows the packets one layer further down. In Wireshark's packet list, *Length* is the Ethernet frame length without the 4 B frame check sequence, and the UDP *Len* in the info column is the UDP payload, that is the RTP header and the codec payload:

$$
L_{\mathrm{frame}} = 14 + 20 + 8 + 12 + L, \qquad L_{\mathrm{UDP}} = 12 + L
$$

where $L_{\mathrm{frame}}$ is the Ethernet frame length [B], 14 B the Ethernet header, $L_{\mathrm{UDP}}$ the UDP payload length [B], and $L$ the codec payload [B]. The codec and the packetization interval of a stream follow from the frame length together with the time between packets: G.711 at 10 ms and G.726-32 at 20 ms both carry 80 B of payload in a 134 B frame, but the first sends 100 packets per second and the second 50.

### From samples to RTP packets

G.711 sends 8 bits per sample instead of the 16 bits of linear PCM, but it does not quantize uniformly. *Companding* divides the amplitude range into eight segments, each twice as wide as the one below it, and every segment into 16 equal steps. The code byte holds the sign, the 3-bit segment number, and the 4-bit step within the segment. Quiet signals are therefore quantized finely and loud ones coarsely, and the signal-to-quantization-noise ratio stays near 38 dB over a range of about 40 dB of signal levels. A uniform 8-bit quantizer loses 6 dB of that ratio with every halving of the amplitude, which makes quiet speech noisy. A-law and μ-law differ in the details of the segments and in how the bits are inverted for transmission.

The RTP header gives the receiver what UDP does not. The *sequence number* increases by one per packet and reveals lost, duplicated, and reordered packets. The *timestamp* is the sampling instant of the first sample in the payload, counted in periods of the codec clock; for G.711 it increases by 160 per 20 ms packet. It places every payload on the timeline of the sender, even after a loss. The *synchronization source* (SSRC) is a random identifier that separates the streams of a session, and the *marker* bit flags the first packet of a talkspurt. RFC 3550 asks for random initial values of the sequence number, the timestamp, and the SSRC.

### Network impairments

Three network impairments affect the received audio and the ease of conversation. Their perceptual effects also depend on the codec, receiver, and speech content.

- **Delay** – the one-way latency from microphone to loudspeaker, including coding, packetization, queueing, propagation, and playout buffering. The guidance in ITU-T G.114 emphasizes keeping conversational delay low. Large delays disrupt turn-taking; a listening-only test does not measure this conversational effect.
- **Jitter** – the variation of delay between consecutive packets, caused by queueing. The receiver absorbs it in a *jitter buffer*, at the cost of additional delay; packets arriving later than the buffer allows are treated as lost.
- **Packet loss** – packets discarded by congested queues or corrupted on the link. In the 20 ms packetization example, each missing packet removes 20 ms of coded speech. A receiver may replace it using packet-loss concealment. Consecutive losses can remove whole syllables, so *bursty* loss can be more disruptive than independent loss at the same average rate.

A receiver measures loss from the sequence numbers. With the wrap-around at 65 535 undone, the number of packets expected is the range of sequence numbers received, and the loss is the share of them that never arrived:

$$
p = \frac{N_{\mathrm{exp}} - N_{\mathrm{rcv}}}{N_{\mathrm{exp}}} \cdot 100, \qquad N_{\mathrm{exp}} = s_{\mathrm{last}} - s_{\mathrm{first}} + 1
$$

where $p$ is the packet loss [%], $N_{\mathrm{exp}}$ the number of packets expected [–], $N_{\mathrm{rcv}}$ the number of distinct packets received [–], and $s_{\mathrm{first}}$ and $s_{\mathrm{last}}$ the lowest and highest sequence numbers received [–]. Losses before the first or after the last received packet are not counted unless the sender's packet count is known.

Jitter is estimated as in RTCP receiver reports (RFC 3550, Section 6.4.1). For every pair of consecutive packets, the spacing at the receiver is compared with the spacing at the sender, and the absolute difference is smoothed with a gain of 1/16:

$$
D_i = (R_i - R_{i-1}) - (S_i - S_{i-1})
$$

$$
J_i = J_{i-1} + \frac{|D_i| - J_{i-1}}{16}
$$

where $D_i$ is the change in transit time between packets $i-1$ and $i$ [s], $R_i$ the arrival time of packet $i$ [s], $S_i$ its RTP timestamp converted to seconds [s], and $J_i$ the jitter estimate after packet $i$ [s]. Wireshark reports the mean and the maximum of this estimate. A fixed delay adds the same amount to every arrival time and leaves the jitter unchanged.

### Traffic control in Linux

The `tc` utility configures the kernel packet scheduler. Every interface has a root *queueing discipline* (qdisc) that decides when outgoing packets are transmitted. The `netem` qdisc emulates network impairments on an otherwise ideal link:

```bash
tc qdisc add dev DEVICE root netem delay TIME loss PERCENT%
```

`dev DEVICE` selects the interface, `root netem` installs netem as the root qdisc, `delay TIME` adds a fixed delay to every outgoing packet, and `loss PERCENT%` drops packets independently at random with the given probability, written in percent (`loss 3%` loses 3 packets in 100). The order of the values matters:

- `delay 100ms 20ms` – the first value is the mean delay, the second the jitter. Without a `distribution` keyword, each packet's delay is drawn *uniformly* from 100 ± 20 ms, that is from 80 ms to 120 ms. `distribution normal` (or `pareto`, `paretonormal`) uses that distribution with the second value as its standard deviation instead.
- `loss 3% 25%` – a second value after `loss` is not a jitter but a *correlation*: the probability of a loss depends by 25 % on whether the previous packet was lost.

A plot of the one-way delay of each packet shows a netem configuration directly: the delays form a band centred on the configured delay, as wide as twice the jitter for the uniform distribution, and lost packets leave gaps in the sequence numbers. Delay and jitter are read from the band, loss from the gaps. See the [netem manual](https://github.com/iproute2/iproute2/blob/main/man/man8/tc-netem.8).

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

For network planning, ITU-T G.107 (the E-model) rates a connection by a transmission rating factor $R$ from 0 to 100 and maps it to an estimated MOS:

$$
\mathrm{MOS} = 1 + 0.035 \cdot R + 7 \cdot 10^{-6} \cdot R \cdot (R - 60) \cdot (100 - R)
$$

where $\mathrm{MOS}$ is the estimated mean opinion score [–] and $R$ the transmission rating factor [–], for $0 < R < 100$ (MOS is 1 at $R \le 0$ and 4.5 at $R \ge 100$). Ranges of $R$ are labelled with user-satisfaction categories, which the mapping turns into MOS ranges. A MOS from a listening test or an objective model can be placed in the same categories, keeping in mind that they were defined for the E-model:

| R [–] | MOS [–] | User satisfaction |
|---|---|---|
| 90–100 | 4.34–4.50 | Very satisfied |
| 80–90 | 4.03–4.34 | Satisfied |
| 70–80 | 3.60–4.03 | Some users dissatisfied |
| 60–70 | 3.10–3.60 | Many users dissatisfied |
| 50–60 | 2.58–3.10 | Nearly all users dissatisfied |
| below 50 | below 2.58 | Not recommended |

The effect of an impairment is reported as the *MOS drop*, the score of the clean reference minus the score of the impaired recording, both from the same method.

These two models estimate listening quality. This experiment does not measure the effect of conversational delay on turn-taking. Similar numerical ranges also do not make ACR MOS, DCR DMOS, and objective estimates interchangeable; compare their trends and explain their different meanings.

## Tasks

### Preparation

Create the environment as described in the [root README](../README.md):

```bash
cd qos-03
uv sync
```

Scapy's `send()` and the in-notebook capture (`sniff()`, `sniff_during()`) open raw sockets, which require the `CAP_NET_RAW` capability. The socket-based sender, the analysis of saved capture files, and the compilation of capture filters need no privileges. Grant the capability once to the interpreter of the environment, not to the `.venv/bin/python` symlink: `readlink -f` resolves the link to the actual executable, which `uv` usually keeps in `~/.local/share/uv/python/`.

```bash
sudo setcap cap_net_raw=eip $(readlink -f .venv/bin/python)
getcap $(readlink -f .venv/bin/python)
uv run python -c "import scapy.all as sa; sa.send(sa.IP(dst='127.0.0.1') / sa.UDP(dport=9) / b'x')"
```

`getcap` should print the path followed by `cap_net_raw=eip`, and the last command should report `Sent 1 packets.` instead of `Operation not permitted`. A Jupyter kernel started before the change keeps its old permissions; restart it. To capture with `tcpdump` as a normal user, grant it the same capability with `sudo setcap cap_net_raw=eip /usr/bin/tcpdump`.

> [!WARNING]
> The capability applies to every program run by that interpreter, including other environments built on the same Python. Remove it when the lab is finished with `sudo setcap -r $(readlink -f .venv/bin/python)`.

> [!NOTE]
> The capability is stored in an extended attribute of the file. It is lost when `uv` replaces the interpreter (for example after `uv python upgrade`), and `setcap` fails on file systems without extended attributes, such as most NFS home directories. In that case, create the environment from a Python on a local disk, `uv venv --python /usr/bin/python3.12` followed by `uv sync`, and grant the capability to that interpreter.

Start JupyterLab and open `qos_03/lab_03.ipynb`, the sender and analysis notebook. The receiving side runs in `qos_03/receiver_03.ipynb`, in a second tab or on the colleague's machine, with the imports and constants already prepared:

```bash
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

Work through section 2 of the notebook. Scapy composes packets layer by layer (`IP() / ICMP() / "text"`), shows them before and after finalization (`show()`, `show2()`, `hexdump()`), sends them (`send()`), and captures them (`sniff()`). The notebook also draws every packet: a byte map colors the hexdump by layer, a table shows which fields Scapy computed, and header diagrams show each header in the 32-bit layout of the RFCs.

1. **Text exchange (2.1).** Rewrite the text exchange over UDP, one character per packet (Task 1), then add random inter-packet delays and random losses to the sender (Task 2).
2. **Audio over RTP (2.2).** The RTP sender is built in steps, each shown before it is used:
   1. Cut `input.wav` into 20 ms blocks and compute the packet and bit rates (Task 3).
   2. Compress the samples with G.711, compare A-law, μ-law, and uniform 8-bit quantization, and listen to the difference (Task 4).
   3. Build the 12-byte RTP header with `struct` and bit shifts, and check it against Scapy (Task 5).
   4. Wrap one block in RTP, UDP, and IP, send it, and decode it in Wireshark with *Decode As*.
   5. Write the loop that numbers and timestamps every packet of the recording (Task 6).
   6. Compare three senders, from naive sleeping to deadline pacing over a UDP socket, by the spacing of their packets, and play the stream in Wireshark (Task 7).
   7. Compare the created stream with the recorded call of Step 1: the SDP codec negotiation, the header fields, the packet spacing, and the RTP headers side by side, then replay the recorded call with the same sender (Task 8).
   8. Optional: receive and play the stream in the notebook, then add loss and a simple packet-loss concealment (Task 9).

The receivers for 2.1, Task 1, and 2.2 are in `receiver_03.ipynb`, since `sniff()` blocks the notebook it runs in. On the loopback interface, Scapy captures every packet twice, once leaving and once arriving; the notebooks pass `lfilter=skip_loopback_copies()` to keep one copy. Verify each step in Wireshark. The reference implementations of the header and the packet loop are `rtp_header` and `rtp_packets` in `lib/core.py`; the notebook imports them only after the corresponding tasks.

### Step 3 – Emulate impairments with `tc`

Each trial applies one netem configuration to the laboratory interface, sends the same 60 s RTP test stream from section 3 of the notebook, and analyzes what was captured. The notebook's `run_trial()` sends the stream, captures it on `IFACE`, saves the capture to `results/trial_<name>.pcap`, and shows the interarrival times with lost and reordered packets marked, the RFC 3550 jitter, the loss-burst lengths, and a summary card. Packets leaving an interface are captured after its qdisc, so a capture on the sender already shows the netem delay and loss; a receiver capture is the authoritative one when available: `receive_trial()` in `receiver_03.ipynb` captures, saves (`results/received_<name>.pcap`), and analyzes the same trial at the receiver.

| Trial | Command (`DEVICE` = laboratory interface) | What to look at |
|---|---|---|
| 3.0 Baseline | none | Spacing and jitter of the unimpaired stream |
| 3.1 Fixed delay | `tc qdisc add dev DEVICE root netem delay 100ms` | Round-trip time in `ping`; spacing at the receiver |
| 3.2 Delay with jitter | `tc qdisc add dev DEVICE root netem delay 100ms 20ms distribution normal` | Spacing, jitter, reordering |
| 3.3 Random loss | `tc qdisc add dev DEVICE root netem loss 3%` | Measured loss, burst lengths |
| 3.4 Bursty loss | `tc qdisc add dev DEVICE root netem loss gemodel P R 100% 0%` | Burst lengths against the geometric distribution |
| 3.5 Optional bottleneck | `tc qdisc add dev DEVICE root netem rate 70kbit limit 50` | Growing delay and drops on a link slower than the stream |

For every trial:

1. Write down a prediction of the loss, the packet spacing, and the jitter (notebook, Task 10).
2. Remove the previous configuration with `tc qdisc del dev DEVICE root` and apply the new one.
3. Run the trial cell and record the measured loss, the mean jitter, and the number of reordered packets next to the prediction.
4. Keep the capture with the complete `tc` command.

For trial 3.4, choose the parameters for a mean loss of 3 % and a mean burst length of 3 packets: the mean burst length $1/R$ gives $R$, and the long-run loss fraction $P/(P+R)$ then gives $P$. With independent loss at probability $p$, a burst ends after each packet with probability $1-p$, so almost every burst is a single packet; under the Gilbert–Elliott model the burst lengths follow a geometric distribution with mean $1/R$. Compare the measured burst histogram with both.

A receiver-only capture shows loss and variation in delay, not delay itself. Measuring absolute one-way delay requires corresponding sender and receiver observations with synchronized clocks; the round-trip time of `ping`, which netem delays in one direction only, is an indirect check of a fixed delay.

### Step 4 – Replay a call under packet loss

The recorded call of Step 1, or the sample call, is sent again through each loss configuration with `replay_rtp()` from section 2.2 g) of the notebook. It resends the UDP payload of every recorded packet unchanged, so the SSRC, the sequence numbers, the timestamps, and the coded speech are those of the call, over a UDP socket to `DST_IP:DST_PORT`, paced by the RTP timestamps. Choose one direction of one G.711 stream with 20 ms packetization, no missing packets, and continuous timestamps (`CALL_PCAP` and `CALL_SSRC` in the notebook); `replay_rtp()` refuses a stream with a timestamp discontinuity.

Replay a clean baseline first, then apply 0.5 %, 1 %, and 3 % independent loss in separate trials. Start the receiver capture before each replay and let it run until the replay has finished.

> [!NOTE]
> The replay can also be done with tcpreplay, a standard tool that resends the packets of a capture file at a chosen rate. It needs root privileges and rewrites the addresses of the recorded packets; at 50 packets/s it offers no timing advantage over the socket sender. See [Appendix – Replaying with tcpreplay](#appendix--replaying-with-tcpreplay).

`receive_replay(model, loss)` in `receiver_03.ipynb` captures one replay and saves it as `results/output_<model>_<loss>.pcap`, where the quality evaluation of the notebook finds it. Check qdisc counters and receiver statistics to establish that the replay passed through the intended impairment. Record observed loss rather than assuming it equals the configured probability. Repeat with bursty loss at comparable mean rates, recording all Gilbert–Elliott parameters. Retain the received captures for reconstruction and comparison.

### Step 5 – Reconstruct and evaluate the audio

Reconstruct the source timeline before evaluating quality. Simply joining the received payloads would remove missing intervals and shorten the recording. RTP timestamps locate audio samples on the source timeline, and sequence numbers help identify missing or repeated packets. See [RFC 3550, Section 2.1](https://www.rfc-editor.org/rfc/rfc3550.html#section-2.1).

For example, if packets at timestamps 0, 160, and 320 carry 160 samples each, losing the middle packet should leave a 160-sample gap. At 8 kHz, that gap is 20 ms; the recording should still last 60 ms.

The supplied [reconstruction utility](reconstruct_rtp.py) decodes G.711, puts received samples at their original offsets, and inserts digital silence for missing packets, including losses at the beginning or end. It uses the complete clean stream to establish the duration. This is an offline loss model: it accepts reordered packets and does not simulate late-packet rejection or a receiver's jitter buffer. Silence insertion is a baseline, not a model of every real receiver's concealment algorithm.

Export the clean stream from the recorded call and one received stream from its replay as tab-separated sequence number, timestamp, and payload fields. Replace `CALL_PCAP`, `CALL_PORT`, and `SSRC` with the recorded capture, the destination port of the chosen stream in it, and its stream identifier, and `DST_PORT` with the notebook constant; the replay preserves the SSRC. The `-d` option makes tshark decode the port as RTP:

```bash
tshark -nr CALL_PCAP -d udp.port==CALL_PORT,rtp -Y "rtp.ssrc == SSRC" \
  -T fields -e rtp.seq -e rtp.timestamp -e rtp.payload > results/reference.tsv
tshark -nr results/output_random_0.5.pcap -d udp.port==DST_PORT,rtp -Y "rtp.ssrc == SSRC" \
  -T fields -e rtp.seq -e rtp.timestamp -e rtp.payload > results/received.tsv
```

For the supplied example, use `CALL_PCAP=pcap/asterisk-echo-test.pcapng`, `CALL_PORT=16088`, `SSRC=0xabd66334`, and `DST_PORT=54321`. The utility expects continuous G.711 audio from one stream, without silence suppression or codec changes. It rejects an incomplete clean timeline. Decode the clean and received exports with the same settings:

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
7. Why does G.711 keep the signal-to-quantization-noise ratio roughly constant over a wide range of levels, and why does a uniform 8-bit quantizer not?
8. A receiver gets RTP packets with timestamps 0, 160, 480, and 320, in this order. What does it conclude, and where does each payload go in the output?

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
10. H. Schulzrinne and S. Casner, "RTP Profile for Audio and Video Conferences with Minimal Control," RFC 3551, 2003.
11. ITU-T Recommendation G.107, *The E-model: a computational model for use in transmission planning*, 2015.

## Task solutions

> [!WARNING]
> Spoiler alert. This section contains the solutions of the notebook tasks. Attempt each task first; compare afterwards.

Measured values depend on the machine, the recording, and the random draws. The figures below were obtained on a laboratory-class Linux computer over the loopback interface, or computed from the configuration; treat them as orders of magnitude, not as targets.

### Task 1 – UDP, one character per packet

Sender (`lab_03.ipynb`):

```python
for char in msg:
    sa.send(ip / sa.UDP(sport=SRC_PORT, dport=DST_PORT) / char, verbose=False)
```

Receiver (`receiver_03.ipynb`):

```python
def print_char(pkt):
    print(pkt["Raw"].load.decode(errors="replace"), end="", flush=True)


sa.sniff(
    iface=IFACE,
    prn=print_char,
    filter=f"udp and dst port {DST_PORT}",
    lfilter=skip_loopback_copies(),
    store=0,
)
```

On the wire, the IP protocol field changes from 1 (ICMP) to 17 (UDP), and the 8 B ICMP header (type, code, checksum, identifier, sequence number) is replaced by the 8 B UDP header (source port, destination port, length, checksum). Each character now travels in its own 29 B IP packet (20 B IP + 8 B UDP + 1 B payload), so 28 of every 29 bytes are header. The receiver's kernel answers an ICMP echo request with an echo reply, but a UDP datagram to a port without a listening socket with an ICMP *port unreachable* message (type 3, code 3), visible in Wireshark; `sniff()` captures the datagram without opening the port.

### Task 2 – Random delay and loss

```python
LOSS = 0.2  # probability of dropping a character [–]
MEAN_GAP = 0.2  # mean inter-packet delay [s]

for char in msg:
    if rng.random() < LOSS:
        continue  # lost: never sent
    sa.send(ip / sa.UDP(sport=SRC_PORT, dport=DST_PORT) / char, verbose=False)
    time.sleep(rng.exponential(MEAN_GAP))
```

In Wireshark, the *Time* or *Delta time displayed* column shows the irregular gaps, increased by the time `send()` itself takes (milliseconds), and on average about 20 % of the characters are missing. The receiver of Task 1 cannot tell that anything is missing: UDP carries no sequence number. Detecting loss requires a counter in the payload, which is what the RTP sequence number provides.

### Task 3 – Packet arithmetic

1. Duration = number of samples / 8000 Hz; packets = ⌈samples / 160⌉. The sample call of README Preparation lasts 21.9 s and needs 1095 packets.
2. Payload 160 B per packet, 50 packet/s, and 160 · 8 · 50 = 64 kbit/s of payload.
3. (160 + 40) · 8 · 50 = 80 kbit/s at the IP layer, of which 40 / 200 = 20 % is header.
4. With 60 ms packets the IP rate falls to 69.3 kbit/s, but every lost packet removes 60 ms of speech, enough for a whole phoneme, and the first sample of each packet waits 60 ms before it can be sent. This packetization delay adds directly to the one-way delay budget of ITU-T G.114, together with the jitter buffer, and makes concealment of a loss much harder.

### Task 4 – A-law against μ-law

Signal-to-quantization-noise ratio of a sine wave (1019 Hz) at several levels, computed with `lib/core.py`:

| Level [dBov] | A-law [dB] | μ-law [dB] | Uniform 8 bit [dB] |
|---|---|---|---|
| −60 | 12.8 | 16.8 | −13.3 |
| −50 | 24.3 | 27.1 | 0.4 |
| −40 | 34.2 | 34.0 | 9.3 |
| −20 | 38.4 | 38.1 | 30.2 |
| −10 | 36.4 | 37.2 | 40.1 |
| 0 | 39.0 | 38.3 | 49.8 |

1. A loud block of speech gives roughly 35–39 dB with either law; a quiet block (pauses, breathing) gives a lower ratio, and μ-law is a few dB better than A-law at the very lowest levels, because its smallest step is finer (8 against 32 in 16-bit units).
2. The uniform quantizer wins only above about −15 dBov, close to full scale. Speech spends most of its time 20–40 dB below full scale, and quiet passages are where uniform quantization noise is plainly audible; G.711 trades a little quality on the loudest peaks for a constant quality everywhere else.
3. Silence: A-law codes of near-zero samples are `d5` / `55` (alternating bits), μ-law codes `ff` / `7f`. The receiver should not guess from the payload, though: the RTP payload type, 8 (PCMA) or 0 (PCMU), states the law.

### Task 5 – Build the header yourself

```python
def my_rtp_header(sequence, timestamp, ssrc, payload_type, marker=0):
    first = (2 << 6) | (0 << 5) | (0 << 4) | 0  # V = 2, P = 0, X = 0, CC = 0: 0x80
    second = (marker << 7) | payload_type  # M and PT
    return struct.pack("!BBHII", first, second, sequence % 2**16, timestamp % 2**32, ssrc)
```

Without the modulo, `sequence=65536` raises `struct.error`, because the `H` format holds 0 to 65535. RTP counters wrap around: after 65535 comes 0, so the function reduces the sequence number modulo 2¹⁶ and the timestamp modulo 2³². With `marker=1` and payload type 8 the second byte is `0x88`.

### Task 6 – Write the packetization loop

```python
payload_type, encode, _ = G711[ENCODING]
ssrc = int(rng.integers(2**32))
my_stream = []
for index, start in enumerate(range(0, len(samples), SAMPLES_PER_PACKET)):
    block = samples[start : start + SAMPLES_PER_PACKET]
    block = np.pad(block, (0, SAMPLES_PER_PACKET - len(block)))
    header = my_rtp_header(
        sequence=index,
        timestamp=index * SAMPLES_PER_PACKET,
        ssrc=ssrc,
        payload_type=payload_type,
        marker=int(index == 0),
    )
    my_stream.append(
        sa.IP(dst=DST_IP)
        / sa.UDP(sport=SRC_PORT, dport=DST_PORT)
        / sa.Raw(header + encode(block).tobytes())
    )
```

The sequence number grows by 1 and the timestamp by 160 per packet; only the first packet carries the marker. Compared with `rtp_packets`, the bytes are identical except for the SSRC (bytes 8–11 of the UDP payload), which each stream draws at random. Scapy shows the student's packets as `Raw` and the reference ones as `RTP`, but on the wire they are the same.

Questions of 2.2 e): the timestamp counts samples, not milliseconds, so it grows by 160 (8000 Hz × 20 ms); a 16 kHz codec with 20 ms packets adds 320. The 16-bit sequence number wraps after 65 536 / 50 ≈ 1311 s, about 22 minutes; the 32-bit timestamp counts 160 times faster and needs the wider field (it wraps after about 6.2 days at 8 kHz). `rtp_packets` randomizes none of them by itself; the notebook passes it a random SSRC and leaves the sequence number and the timestamp at 0. Predictable initial values make it easier to inject forged packets into a stream or to recognize a stream.

### Task 7 – Assess the audio transmission

Spacing of 250 packets sent over `lo` by the three senders:

| Sender | Mean spacing [ms] | Standard deviation [ms] | Minimum / maximum [ms] | RFC 3550 jitter, mean [ms] |
|---|---|---|---|---|
| `send_sleep` | 33.3 | 3.5 | 27.9 / 42.8 | 12.5 |
| `send_paced` | 20.02 | 2.9 | 12.2 / 32.0 | 2.0 |
| `send_socket` | 20.00 | 0.13 | 19.6 / 20.4 | 0.07 |

`send_sleep` is slow because every `sa.send()` opens a raw socket, looks up the route, builds and serializes the packet, and closes the socket, roughly 13 ms here, which adds to every 20 ms sleep: the stream lasts 1.7 times as long as the audio and a receiver's jitter buffer would run dry. `send_paced` keeps the mean exact, because the deadlines do not depend on how long sending took, but the slow `send()` still shifts individual packets by milliseconds. `send_socket` does almost nothing between deadlines and stays within half a millisecond. What remains is the latency of waking a sleeping process (scheduler, timer slack of 50 µs by default, CPU power states), the Python interpreter and its garbage collector, and other load on the machine. Wireshark's jitter agrees with the cards.

### Task 8 – Compare the streams

Values for the sample call; your own capture will differ in details.

| Property | Phone → PBX | PBX → phone | Created |
|---|---|---|---|
| First sequence number | 0 | 9826 | 0 |
| First timestamp | 1781701558 | 160 | 0 |
| Packets with marker bit | 0 | 0 | 1 (the first) |
| DSCP | 0 | 46 (EF) | 0 |
| TTL at the capture point | 64 | 60 | 64 |
| Spacing mean ± std [ms] | 20.000 ± 5.0 | 19.99 ± 1.3 | 20.000 ± 0.13 |
| Timestamp step | 160 | 160, plus 69 once and a jump of 1 781 702 443 | 160 |

1. Fixed by the protocol and the negotiation: the version, the payload type (8, PCMA, accepted in the `200 OK`), the timestamp step of 160 and the payload of 160 B (20 ms of G.711, `ptime:20`). Free choices of the sender: the SSRC, the initial sequence number and timestamp, the use of the marker bit, the DSCP, and the ports, which each side announces in its SDP. The TTL starts at the operating system's default of 64 on both senders; the PBX's packets arrive with 60, which means four routers between it and the capture point if the PBX also starts at 64.
2. Neither recorded sender follows the recommendations fully: the phone randomizes the timestamp but starts the sequence number at 0, the PBX randomizes the sequence number but starts the timestamp at 160. The notebook's stream starts both at 0. Only the notebook sets the marker bit; RTP audio profiles tie the marker to talkspurts after silence suppression, and continuous senders often never set it.
3. The phone's packets come in late/early pairs, about 30 ms and then 10 ms apart, with a mean of exactly 20 ms: the signature of deadline pacing, as in `send_paced`. The phone sends each packet when 20 ms of audio is due by its sample clock; when one packet leaves late (the process woke up late, or the audio device delivered two frames at once), the next one leaves as soon as possible to catch up, so the timing errors do not accumulate.
4. The PBX stream has a 69-sample step (a short last frame of its prompt) and then a timestamp jump of about 1.78 · 10⁹ at 21.0 s, when the echo service stops playing its own audio and starts relaying the caller's packets with their timestamps. The jitter formula reads the jump as a 2.6-day change in transit time; the mean jitter becomes 188 007 ms, here and in Wireshark, and is meaningless. A sender that changes its timing base should set the marker bit so that receivers resynchronize, or better keep the timestamps continuous by translating the relayed ones.
5. DSCP 46, Expedited Forwarding (RFC 3246), asks routers for low-delay, low-loss treatment, typically a strict-priority queue; the PBX marks its voice packets, the phone does not. Mark the created stream with `sa.IP(dst=DST_IP, tos=0xB8)` (0xB8 = 46 · 4, the DSCP sits in the upper six bits of the former ToS byte) or, in `send_socket`, with `sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0xB8)`; no extra privileges are needed. Wireshark shows *Differentiated Services Codepoint: Expedited Forwarding (46)*.

Replay: `compare_streams` shows the replayed stream with the same SSRC, sequence numbers, timestamps, and payloads as the recording; only the addresses and the timing differ. On `lo` the spacing tightened from 20.000 ± 5.0 ms to 20.000 ± 0.14 ms, because the replay is paced by the timestamps, not by the original arrival times. The opposite direction cannot be replayed: `replay_rtp` stops at its timestamp discontinuity.

### Task 9 – Optional: hear the loss, then conceal it

Loss before sending:

```python
kept = [pkt for pkt in stream if rng.random() >= 0.05]
captured = sniff_during(lambda: send_socket(kept), IFACE, f"udp and dst port {DST_PORT}")
received = rtp_stream(captured, dport=DST_PORT)
Audio(decode_rtp(received, ENCODING) / 32768, rate=SAMPLE_RATE, normalize=False)
```

Concealment by repeating the previous packet:

```python
def decode_with_repetition(received, encoding=ENCODING, block=SAMPLES_PER_PACKET):
    audio = decode_rtp(received, encoding)
    present = set((received["ext_ts"] - received["ext_ts"].min()) // block)
    for k in range(1, len(audio) // block):
        if k not in present:  # missing: copy the block before it
            audio[k * block : (k + 1) * block] = audio[(k - 1) * block : k * block]
    return audio
```

With silence, 1 % loss gives occasional clicks, 5 % a clearly choppy voice, and 10 % is hard to follow. Repetition makes single losses nearly inaudible, so 1–5 % usually becomes tolerable; at 10 % bursts are frequent enough to be heard. A repeated 20 ms block is periodic; repeating it several times produces a buzzing, robotic tone. Practical concealment (for example ITU-T G.711 Appendix I) repeats pitch periods instead of whole blocks and fades the signal out after a few tens of milliseconds.

### Task 10 – Predict, run, compare

Expected results of the 60 s, 3000-packet test stream:

| Trial | Loss [%] | Spacing and jitter | Reordered |
|---|---|---|---|
| 3.0 Baseline | 0 | 20 ms ± a fraction of a millisecond; jitter below 1 ms | 0 |
| 3.1 Fixed delay | 0 | As the baseline; `ping` RTT grows by 100 ms | 0 |
| 3.2 Delay with jitter | 0 (raise `settle`) | Spread of tens of ms, some packets almost back to back; jitter about 20 ms | Many, about a quarter of the packets |
| 3.3 Random loss | 3 ± 0.3 | As the baseline, with 40 ms gaps after each loss | 0 |
| 3.4 Bursty loss | about 3, varies strongly | As the baseline, with gaps of several packets | 0 |
| 3.5 Bottleneck | about 18 | Spacing rises to about 24.5 ms; delay grows to about 1.2 s | 0 |

For 3.2: the difference of two independent normal delays with σ = 20 ms has σ = 20√2 ≈ 28 ms, so a packet overtakes its predecessor (difference above 20 ms) with probability 1 − Φ(0.71) ≈ 0.24, and the mean absolute difference, which the jitter estimate approaches, is about 22.6 ms. For 3.3: 3000 packets at p = 0.03 lose 90 on average with a standard deviation of √(3000 · 0.03 · 0.97) ≈ 9 packets. For 3.4, R = 1 / 3 = 33.3 % from the mean burst length of 3 packets, and P = R · p / (1 − p) = 33.3 · 0.03 / 0.97 ≈ 1.03 %. For 3.5, netem counts the 14 B Ethernet header, so the stream needs 214 B · 8 · 50 = 85.6 kbit/s against 70 kbit/s: the queue of 50 packets fills, the delay reaches 50 · 214 · 8 / 70 000 ≈ 1.22 s, packets then leave every 214 · 8 / 70 000 ≈ 24.5 ms, and 1 − 70 / 85.6 ≈ 18 % are dropped. With `rate 90kbit` the link keeps up: no loss and a constant serialization delay of about 19 ms.

### Task 11 – Interpret the trials

1. Delay with jitter changed the spacing; random and bursty loss changed only the number of packets (plus the gap left by each loss); the bottleneck changed both. A fixed delay shifts every arrival by the same amount, so the differences D in the RFC 3550 estimate, and with them the jitter, stay unchanged.
2. Independent loss also produces bursts by chance, with probability p for each further packet: at p = 0.03 about 3 % of the bursts have two packets or more, and the mean burst length is 1 / (1 − p) ≈ 1.03. The histogram is almost entirely at 1, matching the geometric distribution with R = 1 − p = 97 %.
3. At 3 % mean loss and a mean burst of 3 packets, 3000 packets contain only about 30 bursts. The histogram follows the geometric shape roughly, but with so few bursts the relative frequencies scatter by several percentage points and the measured mean loss easily lies between 2 % and 4 %. A longer stream, or several trials pooled, is needed for a firm conclusion.
4. A packet that arrives later than its playout time (here, more than 40 ms after its nominal arrival) is discarded, so the receiver counts it as lost, although the network delivered it. Packets that are reordered but within the buffer are put back in order using their sequence numbers and timestamps and are played normally. Late loss therefore adds to network loss, and a larger buffer trades it for more delay.

### Task 12 – Compare the methods

The numbers depend on the recording and the listeners; the patterns to look for are these. Measured loss differs from the configured value, especially for the Gilbert–Elliott model, so plot and discuss against the measured values as well. PESQ and ViSQOL usually agree on the ordering of clearly different loss rates and may disagree for conditions that are close; check which of them follows the ACR ranking. At the same mean loss, bursty loss removes fewer but longer pieces of speech: whole syllables disappear, which listeners tend to judge as worse, while random loss spreads many short gaps over the recording, which the models may penalize more. Explain your own result with the burst lengths you measured. A conversational test would add the effect of delay on turn-taking: the delay of the bottleneck trial or a large jitter buffer would lower conversational quality, while all listening-only scores, subjective or objective, are blind to delay.

## Appendix – Replaying with tcpreplay

[tcpreplay](https://tcpreplay.appneta.com/) resends the packets of a capture file on an interface. It works on whole frames, so the recorded addresses must be rewritten for the laboratory network and the replay needs root privileges. Prepare `rtp.pcap` containing one direction of one G.711 stream with 20 ms packetization and no missing packets. For the supplied example, export the outgoing stream:

```bash
tshark -nr pcap/asterisk-echo-test.pcapng -Y "rtp.ssrc == 0xabd66334" -F pcap -w rtp.pcap
```

Run `tcpreplay-edit` on the sender, substituting the original capture addresses for `OLD_SRC_IP` and `OLD_DST_IP`, and the laboratory addresses for the other placeholders:

```bash
sudo tcpreplay-edit -i DEVICE -K --loop 1 --timer nano --pps 50 --dlt=enet --fixcsum \
  --srcipmap=OLD_SRC_IP/32:SRC_IP --dstipmap=OLD_DST_IP/32:DST_IP \
  --enet-smac=SRC_MAC --enet-dmac=DST_MAC rtp.pcap
```

`-K` preloads the capture, `--pps 50` requests 50 packets/s, and the map options rewrite the addresses. The supplied capture uses Linux cooked headers; `--dlt=enet` converts them to Ethernet headers, and `--fixcsum` recalculates checksums. See the [tcpreplay-edit manual](https://tcpreplay.appneta.com/reference/man/tcpreplay-edit/). This rate applies to the selected single stream; replaying two directions at 50 packets/s would change their timing. For the supplied stream, the original addresses are `10.100.100.3` and `158.196.146.236`.

The replayed packets keep their original UDP ports, so the receiver captures port 16088 instead of `DST_PORT`: set `DST_PORT = 16088` in `receiver_03.ipynb` for `receive_replay()`, and use the same port for the received stream in the tshark export of Step 5.
