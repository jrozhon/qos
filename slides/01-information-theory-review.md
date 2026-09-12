# Review of Lecture 01: information theory

Reviewed 12 September 2026. Scope: the complete Markdown deck, including speaker notes; mathematical content of its figure generator; and relevant links to Exercises 01 and 03. This is a content review, not a rendered-layout audit. The accepted corrections and teaching improvements were applied on 12 September 2026. The review below records the original findings; its line references refer to the pre-revision version of `01-information-theory.md`. The revised deck has 50 main-route slides and 15 Extras slides, including the later carrier and sideband explanations.

The lecture has a coherent practical progression, useful worked examples, and good prediction/discussion checkpoints. Its central equations are mostly correct. The main weaknesses are explanations that turn useful approximations into universal rules, and a source-coding section that needs a concrete coding example. Correct the high-priority points before teaching; most require changing only a sentence or two.

## Corrections to make before teaching

1. **The letter-guessing strategy is wrong** — lines 1167–1169.

   Asking whether the letter is E gives a highly unbalanced first split: 12.7% versus 87.3%. Being the most common letter does not make it the best first yes/no question. For this style of questioning, aim to split probability mass roughly in half; an optimal full decision tree minimizes expected depth. Do not replace equal-sized alphabet halves with sequential guesses of individual letters.

   Suggested wording: “With unequal probabilities, divide the remaining probability roughly in half, rather than dividing the number of letters in half. Common letters can then receive shorter descriptions.” Introduce a small prefix code to make the point operational. [MIT notes on Huffman coding](https://ocw.mit.edu/courses/18-200-principles-of-discrete-applied-mathematics-spring-2024/mit18_200_s24_lec19.pdf).

2. **4.70 bits is not the average number of separate-letter questions** — line 1121 and the guessing-tree figure.

   For 26 equally likely letters, the optimal binary question tree has six leaves at depth 4 and twenty at depth 5. Its average is `(6×4 + 20×5)/26 = 4.76923` questions. Repeating that experiment does not make the average tend to `log₂26 = 4.70044`.

   Suggested wording: “Five questions suffice in the worst case. A separate-letter code averages about 4.77 bits. Encoding long blocks of independent letters lets the average approach 4.70 bits per letter.” For example, a fixed-length code for a block of `n` letters needs `ceil(n log₂26)` bits. Also replace the figure’s unqualified “log₂ N questions” label with “log₂ N bits of information.”

3. **Source coding needs an average, block-length, and source-model qualification** — lines 1277, 1310, and 1332.

   The summary promises exact achievement of H. Say “can approach H bits per symbol on average using sufficiently long blocks.” For independent identically distributed symbols and an optimal binary prefix code for blocks of length n, `H ≤ E[Lₙ]/n < H + 1/n` (with the deterministic case handled separately). For dependent sources, the relevant limit is the entropy rate, not the marginal single-letter entropy. The 1,000 biased tosses example means roughly 469 bits on average with an appropriate block code and known model; it does not promise that every sequence fits into 470 bits. [MIT information-theory course notes, source coding](https://ocw.mit.edu/courses/6-441-information-theory-spring-2016/5d8f16adc3385c9ff2975b121bd620e4_MIT6_441S16_course_notes.pdf).

4. **The “usable number of levels” is not a derivation of Shannon capacity** — lines 804–811.

   `L ≈ √(1+S/N)` follows by equating the two displayed rate expressions; it is not a general rule for the number of reliably distinguishable modulation levels. Actual error rates depend on constellation geometry, coding, and the target error probability. At S/N = 15, the heuristic gives four real levels, but uncoded 4-PAM does not thereby attain Shannon capacity with arbitrarily small error.

   Keep the noise/spacing intuition and delete the substitution. Suggested bridge: “Closer signal points are harder to distinguish in noise. Shannon’s theorem accounts for coding across many symbols and gives the ultimate reliable information rate.” The capacity result assumes a bandwidth constraint, average received signal-power constraint, and additive white Gaussian noise. [Shannon’s original paper, continuous-channel coding](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf).

5. **Separate real amplitude levels from QAM constellation points** — lines 609, 628–659, 673–690, and 1375.

   `2B log₂L` is the ideal zero-ISI result for real low-pass PAM with L amplitude levels, bandwidth B, and zero excess bandwidth. It is not a universal symbol-rate formula with any modulation’s constellation size substituted for L. QPSK has four phase states, not four amplitude levels; 16-QAM has sixteen two-dimensional points. For ideal passband QAM, symbol rate is approximately B, and each symbol labels `log₂M` coded bits. With raised-cosine roll-off α, the occupied passband width is `(1+α)Rₛ`.

   Label the Nyquist slide “Ideal baseband PAM” and use that model for its numerical example. In the modulation table, call L/M “distinct signal states.” Keep the baseband/passband distinction in a short note; students do not need a full modulation lecture. [Tse and Viswanath, chapter 7, continuous-time MIMO model and complex baseband sampling](https://web.stanford.edu/~dntse/Chapters_PDF/Fundamentals_Wireless_Communication_chapter7.pdf).

6. **Raw line rate is not always below C** — lines 1019–1033.

   Capacity bounds reliable information rate. A raw coded bit stream can include enough redundancy that its bit rate exceeds C while its useful information rate remains below C. With code rate r and raw coded bit rate Rraw, the relevant information rate is `r Rraw` before other overheads. Rename the box “Net information rate after channel coding,” or explicitly define the raw/net distinction. Define throughput at a particular measurement layer; header subtraction otherwise becomes ambiguous. Codec output is usually application payload, so “minus codec overhead” is not a general goodput rule. [Shannon’s channel-coding theorem](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf).

7. **33.6 kbit/s is not a universal telephone-channel Shannon limit** — lines 971–999.

   Your chosen parameters give 32.9566 kbit/s. They do not prove that 33.6 kbit/s is “exactly where Shannon says”; under those exact assumptions 33.6 would exceed C. Capacity changes with bandwidth, noise, and the channel model. Keep the useful distinction between the analog voiceband circuit and the digital PCM transport.

   Suggested wording: “For these illustrative parameters, the analog voiceband channel has about 33 kbit/s capacity. G.711’s 64 kbit/s digital representation travels over a different channel in the network.” Then, optionally: “V.34 reached 33.6 kbit/s under suitable conditions. V.90 exploited digital-network access for up to 56 kbit/s downstream; it obeyed the capacity limit for that different channel.” V.92 also allowed up to 48 kbit/s upstream. Replace “cheated” and “dial-up stopped at 33.6.” [ITU V.90](https://www.itu.int/rec/T-REC-V.90), [ITU V.92 summary](https://www.itu.int/rec/dologin_pub.asp?id=T-REC-V.92-200011-I%21%21PDF-E&lang=f&type=items).

8. **MIMO needs per-stream SNR and channel-rank qualifications** — lines 1062–1085.

   The multiplier formula is a useful special case if each separable stream has the stated SNR. It is misleading with S interpreted as the original total signal power. A more transparent undergraduate expression is `C = B Σᵢ log₂(1+SNRᵢ)` for the equivalent parallel spatial modes under a specified power allocation. Equal per-mode SNR gives the simple multiplier. With fixed total transmit power, that power must be allocated among modes; channel gains and noise also matter. Avoid promising automatic linear scaling with antenna count “without more power.” [Tse and Viswanath, chapter 8](https://web.stanford.edu/~dntse/Chapters_PDF/Fundamentals_Wireless_Communication_chapter8.pdf).

   “Line of sight means one channel” additionally needs the compact-array, far-field, single-path assumptions. Suitable geometry or polarization can support multiple line-of-sight streams. Say “Closely spaced, co-polarized arrays in a far-field single-path channel may provide only one useful spatial mode.” The existing warning that antenna count alone guarantees nothing is worth retaining. [Tse and Viswanath, chapter 7, sections 7.2.3–7.2.4](https://web.stanford.edu/~dntse/Chapters_PDF/Fundamentals_Wireless_Communication_chapter7.pdf).

9. **Remove the claim that there is nothing to gain above 30 dB** — speaker notes, line 896.

   The displayed formula gives about 9.967 bit/s/Hz at 30 dB and 13.288 at 40 dB: a further 3.321 bit/s/Hz. Diminishing returns do not become zero returns at 30 dB. Low SNR also does not by itself establish that spreading is the right strategy. Replace with “More power brings diminishing capacity gains; practical choices depend on bandwidth, power, interference, and implementation constraints.” Qualify the visible tenfold-power rule as a high-SNR approximation with unchanged propagation and noise.

10. **Companding is amplitude compression/expansion; the bit-equivalence claim is too broad** — lines 359–382 and 417.

   Replace “not compression” with “Companding compresses amplitude range before quantization and expands it after decoding; G.711 still produces a fixed 64 kbit/s stream.” The intended distinction from additional statistical or predictive bit-rate compression is useful. “8 bits perform like 12–13 uniform bits” should be removed or restricted to a precisely specified dynamic-range/small-signal-resolution comparison; it is not full-range uniform-quantizer accuracy. [MIT PCM lecture, nonuniform quantization](https://ocw.mit.edu/courses/16-36-communication-systems-engineering-spring-2009/d91cdcc10683c573cc668c5b1ab3aab6_MIT16_36s09_lec04.pdf).

   The 6 dB/bit rule is fine as a rule of thumb, but specify fixed full-scale range and a suitable input. For an ideal uniform ADC with a full-scale sine, `SQNR ≈ 6.02b + 1.76 dB`, giving approximately 50 and 98 dB for 8 and 16 bits. Your 48/96 values are rough 6b estimates, not universal SQNR values. [Analog Devices MT-001](https://www.analog.com/media/en/training-seminars/tutorials/mt-001.pdf).

## Smaller corrections and qualifications

| Location | Finding and suggested change |
|---|---|
| 127–133; 1041 | Capacity is fixed **for specified channel conditions and resource constraints**. QoS manages delay, jitter, loss, fairness, and service requirements as well as rate allocation. Avoid defining it entirely as sharing bandwidth. |
| 225 | Regeneration removes accumulated analog perturbations **when the symbol decision is correct**. It can also regenerate an erroneous decision. |
| 292–302 | The strict sampling inequality is a good safe statement. Say “exact reconstruction of the band-limited waveform from ideal, unquantized samples”; actual PCM adds quantization error. Keep this as low-pass sampling rather than a universal statement about all bandpass sampling schemes. |
| 326–343 | The 3 kHz alias is correct. For a zero-phase 5 kHz sine, the matching 3 kHz sine is phase reversed. The generator already implements the sign correctly; optionally mention it if students calculate the samples. |
| 473 | Flat PSD over a finite band does not imply independence at every possible sampling interval. Say “White: flat PSD over the modelled band. In our discrete-time simulation, noise samples are independent Gaussian draws.” Band-limiting can correlate samples; whiteness alone implies uncorrelatedness, with independence following under a joint Gaussian model. |
| 507–510 | `A²/2` is the sine’s period/time-average power; `σ²` is expected zero-mean noise power. Finite-record estimates fluctuate and can depend on sampling alignment. Label the plotted values “theoretical powers” so students do not expect exact equality from their noise realization. |
| 628–648 | S and N have just meant signal and noise power; now they mean symbol rate and bits per symbol. Use `R_b = R_s log₂M`, reserving S and N for power. |
| 747–776 | `kTB` is available thermal noise power into a matched load in the classical regime, over the effective noise bandwidth. Specify this once. The wideband limit assumes fixed **received** S, not merely fixed transmit power. The table’s first-to-last difference is 58.1 dB, approximately 60 dB. The displayed wideband limit is correct under the model. [Nyquist’s original thermal-noise paper](https://123.physics.ucdavis.edu/johnson_files/nyquist_1928.pdf). |
| 937 | Replace “bits per symbol per hertz” with “`C/B = log₂(1+S/N)` is spectral efficiency, measured in bit/s/Hz.” |
| 955–966 | The “Carrier” column mixes a passband, frequency ceilings, and carrier frequencies. Rename it “Frequency range / carrier,” or omit it because carrier frequency is not an independent input to this formula. Keep every SNR explicitly hypothetical. For DSL, distinguish an upper spectrum edge from the usable bandwidth of a direction, and note per-tone SNR variation. |
| 962 | The 5G mmWave row mixes incompatible examples. At 28/38 GHz, standard FR2-1 component-carrier widths reach 400 MHz; FR2-2 n263 supports widths up to 2,000 MHz in a different band. A 72 GHz carrier does not fit n263’s 57–71 GHz range. Use a clearly specified example such as “NR FR2-1, 28 GHz, 400 MHz,” or label the row as a hypothetical wideband radio rather than 5G. Aggregated bandwidth must be identified separately. [ETSI TS 138 104 v19.2.0, tables 5.3.5-2/3 and 5.2-2](https://www.etsi.org/deliver/etsi_ts/138100_138199/138104/19.02.00_60/ts_138104v190200p.pdf). |
| 1047 | The Wi-Fi 1.2/0.7/0.5 Gbit/s sequence is not a general conversion between rate layers. PHY rate requires stream count, modulation, coding, guard interval, and channel width; measured throughput also depends on traffic and contention. Replace with the reproducible G.711 packet calculation below. |
| 1216 | Keep the thermodynamic analogy optional. The von Neumann anecdote is unsourced here and its attribution is disputed; omit it or explicitly identify it as a reported anecdote with a traceable source. Do not present the quotation as established history. |
| 1232–1258 | Add `0 log₂0 := 0`. Strictly `H(X)` is measured in bits; “bits per source symbol” is the operational interpretation used here. “Carries nothing” assumes the deterministic source and its framing are already known to the receiver. |
| 1293–1296 | The 26-letter figures 4.70, about 4.1, and about 3.6 agree with Shannon’s 1951 table. The long-context estimate is not a universal constant; the paper reports experimental bounds, including roughly 0.6–1.3 for its long-context experiment, which uses a 27-symbol alphabet including space. Flag the alphabet/model change. [Shannon 1951](https://fizyka.umk.pl/~milosz/KKK/shannon-1951.pdf). |
| 1305–1319 | An arbitrary text character is not always one byte. Say “plain ASCII text stored one byte per character.” ZIP/LLM compression results need a corpus, model, coding method, and overhead convention; remove “ZIP recovers most” and the unreferenced sub-one-bit claim. A model’s achieved coding rate or cross-entropy is not automatically the source’s true entropy. |
| 1332–1352 | Distinguish lossless source coding from lossy speech coding. G.711 quantization and Opus do not preserve the original analog waveform exactly. Add: “Lossy codecs can use fewer bits by accepting distortion.” |
| 1393 | “A symbol only carries a full bit when unpredictable” should say **binary symbol**; a uniform four-valued symbol has two bits of entropy. |

The history is broadly appropriate, but “four results, all in this lecture” overstates coverage of the stability criterion, which is only named. The Nyquist patent/career details are supported by the contemporary [Bell Laboratories Record, November 1960](https://www.worldradiohistory.com/Archive-Bell-Laboratories-Record/60s/Bell-Laboratories-Record-1960-11.pdf). Change “Fifty years of coding theory” to “Decades of coding theory,” especially because the list includes polar codes.

Two figure-source details need attention when the deck is revised:

- `slides/scripts/generate-figures.py`, symbols figure: its embedded description says equal symbol rate and doubled bit rate; the actual diagram correctly shows equal bit rate and halved symbol rate. Make the description match the drawing and the Markdown alt text.
- Capacity-versus-bandwidth figure: the footer says doubling B doubles C if noise power does not grow. The correct condition is fixed **SNR**; both signal and noise power can grow together. Use exactly the same assumption in the caption and slide.

## What is already correct

The PCM sequence, 8 kHz × 8 bits = 64 kbit/s, 125 µs sample period, and 20 ms → 160 bytes → 50 packets/s calculations are correct and align with Exercise 03. The alias frequency is 3 kHz. The Gaussian density, SNR conversions, entropy formula and bounds, and binary entropy curve are correct with the qualifications above.

Independent recomputation also confirms:

| Example | Result |
|---|---|
| 20 dB linear SNR | 100 |
| `log₂(101)` versus erroneous `log₂(21)` | 6.658 versus 4.392; approximately 34% underestimate |
| B = 3,000 Hz, S/N = 15 | 12,000 bit/s; SNR = 11.761 dB |
| B = 3,100 Hz, S/N = 1,585 | 32,956.65 bit/s |
| Thermal floor at 290 K, 3.1 kHz / 20 MHz / 2 GHz | approximately −139.06 / −100.96 / −80.96 dBm |
| Self-information of E and Z using the stated probabilities | 2.977 and 10.480 bits; Z rounds to **10.5**, rather than 10.4, to one decimal place |
| Binary entropy at p = 0.1 | 0.468996 bits per independent toss |

The Opus 6–510 kbit/s range is supported by [RFC 6716](https://www.rfc-editor.org/rfc/rfc6716.html). It is a codec operating range, not a lossless representation bound for speech.

## Undergraduate teaching improvements

1. **Give students four observable outcomes.** By the end they should be able to compute a PCM source rate; convert SNR and calculate an AWGN capacity bound; distinguish source rate, coded line rate, and delivered payload rate; and calculate entropy for a small discrete source. The roadmap already explains the topics; these outcomes explain what students should be able to do.

2. **Make G.711 the recurring example.** Trace microphone → anti-alias filter → sampler → quantizer → 64 kbit/s source → packets → link → playout. On each return, mark which quantity is being discussed. This also prevents students from treating the speech’s 3.1 kHz bandwidth as the transport link’s bandwidth.

3. **Replace the Wi-Fi throughput anecdote with packet arithmetic from the lab.** With 20 ms G.711 packets, use `(160 + 12 + 8 + 20) × 8 × 50 = 80,000 bit/s` at the IPv4 layer, excluding link overhead and assuming no options. The payload remains 64 kbit/s. Ask what changes at 40 ms: `(320+40) × 8 × 25 = 72,000 bit/s`. Students can see the overhead/packetization-delay tradeoff. This calculation is already documented in `qos-03/README.md`.

4. **Add one complete entropy-and-code example before English.** Use this four-outcome source:

   | Outcome | Probability | Self-information | Prefix code | Code length |
   |---|---|---|---|---|
   | A | 1/2 | 1 bit | 0 | 1 |
   | B | 1/4 | 2 bits | 10 | 2 |
   | C | 1/8 | 3 bits | 110 | 3 |
   | D | 1/8 | 3 bits | 111 | 3 |

   Have students calculate `H = 0.5×1 + 0.25×2 + 0.125×3 + 0.125×3 = 1.75` bits/symbol, then compare with a two-bit fixed-length code. Decode a short bit string together. This teaches surprise, average information, short descriptions for common outcomes, and unambiguous decoding without requiring a Huffman algorithm lesson.

5. **Demonstrate dependence explicitly.** Compare independent fair bits with a known alternating sequence `010101…`. Both can have equal observed counts of zeros and ones, but the alternating sequence is predictable once the phase is known. Explain that single-symbol frequencies miss structure across time. Then the English-context slide becomes a consequence rather than an unexplained table.

6. **Distinguish three meanings of encoding.** PCM encoding labels quantized samples; source coding removes statistical redundancy; channel coding introduces controlled redundancy for error protection. A small three-row comparison is sufficient. Without it, “compression removes bits” and “coding adds bits” can sound contradictory.

7. **Show what the theorem’s idealization costs.** One sentence is enough: “Approaching capacity generally requires long, sophisticated codes; finite delay and complexity leave a practical gap.” Tie this to voice latency. Explain that source entropy measures uncertainty under a model, not the importance or truth of a message.

8. **Protect time for reasoning.** There are 51 slides, including cover, dividers, references, and closing. That can fit 90 minutes, but the quantitative and conceptual core needs discussion time. Keep the existing checkpoints. Move the Nyquist biography and technology survey to backup; keep MIMO’s qualitative answer because the lab asks about it, with the equation as optional extension. Keep the wideband-noise insight but make its limit calculation optional.

   A workable 90-minute allocation is 5 minutes for motivation; 18 for signals/PCM; 15 for noise/SNR; 20 for symbols/capacity; 10 for network-rate distinctions and qualitative MIMO; 17 for information/entropy; and 5 for an exit question and exercise setup. Checkpoints are included in those blocks.

9. **End with transfer questions, not only formula recall.** Examples: “Does 0 dB SNR mean zero capacity?”; “Does doubling bandwidth double capacity if received signal power is fixed?”; “Can a binary source have less than one bit of entropy per symbol?”; and “Why is a 64 kbit/s voice payload an 80 kbit/s IPv4 stream?”

10. **Attach assumptions to equations and keep notes consistent.** A one-line tag such as “AWGN; fixed received average power; noise measured over B” is enough. Fix misleading statements in speaker notes as well as visible slides. Add Shannon 1951 to the references, since it is used explicitly, and cite any retained technology or performance figures on their own slide.

The highest-value revision is to retain the present overall sequence, fix the ten priority items, replace the English guessing claim with the four-symbol coding example, and use the lab’s G.711 overhead calculation to connect information theory to QoS.
