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

## Theory

### Anatomy of a VoIP call

A VoIP call consists of two independent flows. *Signaling* establishes, modifies, and terminates the session; in this course it is the Session Initiation Protocol (SIP), carried over UDP or TCP, whose messages (`INVITE`, `200 OK`, `ACK`, `BYE`) also negotiate the codec and transport addresses of the media. *Media* is carried by the Real-time Transport Protocol (RTP) over UDP. Each RTP packet has a 12-byte header containing a payload type, a sequence number, a timestamp, and a synchronization source identifier (SSRC), followed by a block of coded audio.

With the G.711 codec of [Exercise 01](../qos-01/README.md#pulse-code-modulation), speech is sampled at 8 kHz with 8 bits per sample and packetized every 20 ms. One packet therefore carries 160 samples, that is 160 B of payload; with the 12 B RTP, 8 B UDP, and 20 B IP headers it is 200 B long. The call produces 50 packets per second in each direction, a 64 kbit/s payload stream and an 80 kbit/s IP stream:

$$
R_{\mathrm{IP}} = \frac{(160 + 12 + 8 + 20) \cdot 8}{0.02} = 80\,000 \ \mathrm{bit/s}
$$

where the numerator is the packet length in bits and the denominator the packetization interval [s]. The payload type field distinguishes A-law (PCMA, type 8, used in Europe) from μ-law (PCMU, type 0).

### Network impairments

Three properties of the network path determine the quality of the received audio.

- **Delay** – the one-way latency from microphone to loudspeaker, including coding, packetization, queueing, propagation, and playout buffering. ITU-T G.114 recommends at most 150 ms for interactive conversation; above about 400 ms, turn-taking breaks down. Delay is invisible in a one-way (listening) test and dominant in a conversational test.
- **Jitter** – the variation of delay between consecutive packets, caused by queueing. The receiver absorbs it in a *jitter buffer*, at the cost of additional delay; packets arriving later than the buffer allows are treated as lost.
- **Packet loss** – packets discarded by congested queues or corrupted on the link. A lost G.711 packet removes 20 ms of speech. Random loss at a few percent is audible but intelligible; *bursty* loss of the same average rate removes whole syllables and is judged far worse.

### Traffic control in Linux

The `tc` utility configures the kernel packet scheduler. Every interface has a root *queueing discipline* (qdisc) that decides when outgoing packets are transmitted. The `netem` qdisc emulates network impairments on an otherwise ideal link:

```bash
tc qdisc add dev DEVICE root netem delay TIME loss PERCENT%
```

`dev DEVICE` selects the interface, `root netem` installs netem as the root qdisc, `delay TIME` adds a fixed delay to every outgoing packet, and `loss PERCENT%` drops packets independently at random with the given probability. Jitter is added by giving `delay` a second argument, the standard deviation, for example `delay 100ms 20ms`.

Bursty loss is emulated with the Gilbert–Elliott model, a two-state Markov chain that alternates between a *good* state with no loss and a *bad* state in which packets are lost:

```bash
tc qdisc add dev DEVICE root netem loss gemodel P R
```

where `P` is the probability of moving from the good to the bad state after a packet and `R` the probability of returning from bad to good, both in percent. A small `R` relative to `P` produces long loss bursts.

The current configuration is shown with `tc qdisc show dev DEVICE` and removed with `tc qdisc del dev DEVICE root`; the interface then returns to its default behavior.

> [!WARNING]
> `tc` requires superuser privileges (`sudo`). Apply it only to the second, laboratory interface of the server, never to the interface carrying the SSH session, and delete the qdisc when the measurement is finished.

### Speech quality assessment

Quality is measured either by asking listeners (*subjective* methods, ITU-T P.800) or by algorithms that predict what listeners would say (*objective* methods). Both report a mean opinion score (MOS) on a five-point scale from 1 (bad) to 5 (excellent).

- **Absolute Category Rating (ACR)** – each degraded sample is played once and rated on its own. Simple and fast, but sensitive to the listener's expectations.
- **Degradation Category Rating (DCR)** – samples are played in pairs, the unimpaired reference first, and the listener rates the *degradation* of the second relative to the first (also called Double Stimulus Impairment Scale). More sensitive to small impairments.
- **PESQ** (ITU-T P.862) – an intrusive objective model that compares the degraded signal with the reference and outputs a MOS-like score. The reference implementation is available in C.
- **ViSQOL** (Virtual Speech Quality Objective Listener) – an open-source intrusive model from Google. It aligns the degraded signal with the reference, compares their spectrograms with a similarity measure (NSIM), and maps the similarity to a MOS-LQO score with a model trained on listening tests. It has a *speech* mode for narrow- and wide-band speech and an *audio* mode for 48 kHz music and general audio.

Objective models are calibrated on listening tests and therefore do not account for delay; conversational effects must be judged separately.

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

A sample capture of a call to the echo service is provided in `qos_03/pcap/asterisk-echo-test.pcapng`.

### Step 1 – Make a call and capture it

Start a Wireshark capture on the local interface and place a call to the laboratory Asterisk PBX with the SIP credentials distributed through the LMS. Call a colleague's extension or the echo service at extension `*43`. In the capture, identify the SIP dialog and the RTP streams (*Telephony → VoIP Calls* and *Telephony → RTP → RTP Streams*), locate the codec and the payload inside an RTP packet, and map every protocol seen to its layer of the TCP/IP stack.

### Step 2 – Build a traffic generator

Work through the notebook. Scapy composes packets layer by layer (`IP() / ICMP() / "text"`), shows them before and after finalization (`show()`, `show2()`, `hexdump()`), sends them (`send()`), and captures them (`sniff()`). Then complete the notebook tasks: rewrite the text exchange over UDP sending one character per packet, add random inter-packet delays and random losses to the sender, and run `send_audio_as_rtp()` to transmit `input.wav` as G.711 in RTP. Verify each step in Wireshark, and note the timing precision Scapy can achieve from Python.

### Step 3 – Emulate impairments with `tc`

On the laboratory interface, apply netem qdiscs with fixed delay, delay with jitter, random loss, and Gilbert–Elliott loss. Send traffic from Step 2 through the interface and confirm each impairment in a capture at the receiver.

### Step 4 – Replay a call under packet loss

Prepare a clean capture containing only the RTP audio of a call. Replay it with `tcpreplay-edit` towards a colleague's server while the netem qdisc imposes 0.5 %, 1 % and 3 % random loss, and capture it there with `tcpdump`. The addresses and MAC addresses in the file must be rewritten to match the laboratory network:

```bash
sudo tcpreplay-edit -i DEVICE -K --loop 1 --timer nano --pps 50 \
  --srcipmap=127.0.0.1/32:SRC_IP --dstipmap=127.0.0.1/32:DST_IP \
  --enet-smac=SRC_MAC --enet-dmac=DST_MAC rtp.pcap
```

`-K` preloads the file into memory, `--timer nano` uses high-resolution timing, `--pps 50` enforces the G.711 packet rate, and the map options rewrite the IP and Ethernet addresses. In Wireshark, read the loss, delay, and jitter statistics of each received stream.

### Step 5 – Extract and evaluate the audio

Extract the payload of each received stream and convert it to WAV. `tshark` lists the RTP streams, or the UDP conversations if no SIP is present to identify them; the payload is dumped as hexadecimal, converted to raw bytes, and decoded by `ffmpeg`:

```bash
tshark -nr input.pcap -q -z rtp,streams
tshark -nr input.pcap -q -z conv,udp
tshark -nr input.pcap -Y "rtp.ssrc == SSRC" -T fields -e rtp.payload > payload.txt
tshark -nr input.pcap -d udp.port==PORT,rtp -Y rtp -T fields -e rtp.payload > payload.txt
xxd -r -p payload.txt > payload.raw
ffmpeg -f alaw -ar 8000 -ac 1 -i payload.raw output.wav
```

The third and fourth commands are alternatives: select the stream by SSRC, or force RTP decoding on a known UDP port. Use `-f mulaw` for PCMU payloads.

Rate the recordings with ACR and with DCR against the clean reference, then score them with PESQ. The PESQ reference implementation is compiled from its C sources (link in References) with

```bash
gcc -o PESQ *.c -lm -fcommon
./PESQ +8000 reference.wav degraded.wav
```

Tabulate MOS against loss rate and loss model, and compare the subjective and objective scores.

### Step 6 – Score with ViSQOL

ViSQOL provides a second objective score for the same recordings. It is built from source with Bazel; the repository also ships a Dockerfile that performs the build in a container.

```bash
git clone https://github.com/google/visqol.git
cd visqol
bazel build :visqol -c opt
```

The speech model expects 16 kHz input, so both the reference and every degraded file from Step 5 are resampled first. The comparison is then run in speech mode; the `--use_unscaled_speech_mos_mapping` flag reports the score on the full 1–5 range rather than the compressed range calibrated for the model's training set.

```bash
ffmpeg -i reference.wav -ar 16000 reference16.wav
ffmpeg -i output.wav -ar 16000 output16.wav
./bazel-bin/visqol --reference_file reference16.wav --degraded_file output16.wav \
  --use_speech_mode --use_unscaled_speech_mos_mapping
```

Several pairs are scored in one run from a CSV file with `reference,degraded` columns:

```bash
./bazel-bin/visqol --batch_input_csv pairs.csv --results_csv results.csv \
  --use_speech_mode --use_unscaled_speech_mos_mapping
```

The *Quality evaluation* section at the end of the notebook automates Steps 5 and 6: given the recordings in `qos_03/results/` and the paths to the two executables, it scores every file with `score_pair()` from `lib/core.py`, assembles the table together with the hand-entered network statistics and ACR/DCR ratings, and plots MOS against packet loss for all four methods.

Add the ViSQOL column to the table from Step 5. Both PESQ and ViSQOL predict listening quality only, but they weigh impairments differently: ViSQOL is generally more tolerant of small time shifts and more sensitive to spectral distortion. Note where the two models disagree, and which of them tracks the ACR and DCR ratings more closely for random and for bursty loss.

## Questions

1. Which layer of the TCP/IP stack does each of SIP, RTP, UDP, and IP belong to, and which of them carries the codec information?
2. What is the IP-level bit rate of a G.711 call in both directions, and how does it change if the packetization interval is 40 ms?
3. Why does Scapy fail to produce accurate 20 ms packet spacing, and what does a real VoIP client do differently?
4. Two links have the same 3 % average loss, one random and one Gilbert–Elliott with a long bad state. Which yields the lower MOS, and why?
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
