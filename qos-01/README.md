# Exercise 01 – Signals, noise, and channel capacity

This exercise establishes the vocabulary used throughout the course. It introduces the signal as the carrier of information, the conversion of an analog signal into a digital one by pulse-code modulation, Gaussian noise as the basic model of a disturbance, and the Shannon–Hartley formula that bounds the information rate of a noisy channel. In the practical part, students model a harmonic signal corrupted by noise, compute its signal-to-noise ratio and channel capacity, and apply noise to real audio and image data.

## Learning objectives

- Classify signals as analog or digital, continuous-time or discrete-time, periodic or aperiodic, deterministic or random.
- Describe the three steps of pulse-code modulation and state the sampling theorem.
- Characterize Gaussian noise by its probability density function and standard deviation.
- Compute signal power, signal-to-noise ratio, and channel capacity from a sampled signal.
- Relate the bandwidth and signal-to-noise ratio of common access technologies to their achievable data rates.

## Theory

### Signal

A signal is a physical quantity that varies in time (or space) and carries information. In telecommunications it is typically a voltage, a current, or an electromagnetic wave; in information theory it is the sequence of channel states that encodes a message. A communication system consists of a *transmitter* that encodes a message into a signal, a *channel* that carries it, and a *receiver* that decodes it. In telephony, for example, the microphone converts speech into an electrical signal, the network transports it, and the earpiece converts it back into sound.

Signals are classified along several independent axes:

| Criterion | Classes | Example |
|---|---|---|
| Amplitude | *Analog* – any value in a continuous range; *digital* – a finite set of values, usually binary codes | microphone output; computer data |
| Time | *Continuous-time* – defined at every instant; *discrete-time* – defined only at sampling instants | voltage on a wire; samples in a WAV file |
| Repetition | *Periodic* – repeats with period $T$; *aperiodic* – does not repeat | sine wave; single pulse |
| Predictability | *Deterministic* – described exactly by a function; *random* – described only statistically | $\sin(2\pi f t)$; thermal noise |

![Continuous-time signal](fig/continuous.png)

![Discrete-time signal obtained by sampling](fig/discrete.png)

Two quantities describe a periodic signal: the period $T$ [s], the duration of one repetition, and the frequency $f = 1/T$ [Hz], the number of repetitions per second.

### Pulse-code modulation

Pulse-code modulation (PCM) converts an analog signal into a digital one in three steps.

1. **Sampling.** The continuous signal is read at regular instants spaced by the sampling period $T_s$, or equivalently at the sampling frequency $f_s = 1/T_s$. The result is a finite sequence of analog samples.
2. **Quantization.** Each sample is rounded to the nearest of a finite set of levels. The result is a sequence of samples with a finite number of values, each representable by a binary code. The rounding error is called *quantization noise*.
3. **Coding.** The binary codes are replaced by a code better suited to storage, transmission, or compression (for example the A-law or μ-law companding used in telephony, or MPEG audio coding).

Sampling is lossless only when the signal contains no frequency above $f_{\max}$ and the sampling frequency satisfies the sampling theorem (Nyquist–Shannon–Kotelnikov):

$$
f_s \geq 2 f_{\max}
$$

where $f_s$ is the sampling frequency [Hz] and $f_{\max}$ the highest frequency present in the signal [Hz]. If the condition is violated, components above $f_s/2$ are folded back into the lower band; this distortion is called *aliasing*.

> [!NOTE]
> Telephone speech is band-limited to 300–3400 Hz and sampled at $f_s = 8$ kHz with 8-bit quantization, giving the 64 kbit/s PCM stream of the G.711 codec. This stream is the payload of the RTP packets examined in Exercise 03.

### Gaussian noise

Noise is an unwanted random signal added to the useful one. The most common model is *Gaussian noise*, whose amplitude at any instant is a random variable with the normal distribution

$$
p(x) = \frac{1}{\sigma \sqrt{2\pi}} \, e^{-\frac{(x - \mu)^2}{2\sigma^2}}
$$

where $x$ is the noise amplitude, $\mu$ its mean (zero for noise), and $\sigma$ its standard deviation, the square root of the variance $\sigma^2$. The standard deviation measures how far the noise typically departs from its mean and therefore how strong it is.

![Probability density function of the normal distribution](fig/normal.png)

![Harmonic signal with additive Gaussian noise of variance 0.1](fig/noise.png)

When the noise is additionally *white*, its samples are mutually independent and its power is spread evenly over all frequencies. Additive white Gaussian noise (AWGN) is the standard channel model used in the next section.

### Signal power and signal-to-noise ratio

For a discrete signal of $n$ samples $x_1, \dots, x_n$ the mean power is

$$
P = \frac{1}{n} \sum_{i=1}^{n} x_i^2
$$

where $P$ is the power [W] when $x_i$ are voltages across a 1 Ω load; the same expression serves as a relative measure otherwise. The signal-to-noise ratio (SNR) is the ratio of signal power to noise power,

$$
\mathrm{SNR} = \frac{S}{N}
$$

where $S$ is the signal power [W] and $N$ the noise power [W]; the ratio itself is dimensionless [–].

### Channel capacity

The Shannon–Hartley theorem gives the highest rate at which information can be transmitted over an AWGN channel with an arbitrarily small error probability:

$$
C = B \log_2 \left( 1 + \frac{S}{N} \right)
$$

where $C$ is the channel capacity [bit/s], $B$ the channel bandwidth [Hz], and $S/N$ the linear signal-to-noise ratio [–]. Capacity grows linearly with bandwidth but only logarithmically with SNR; doubling the bandwidth doubles the capacity, whereas doubling the SNR adds only one bit per second per hertz.

The table lists the bandwidth and typical linear SNR of several access technologies. Multi-channel systems (ADSL, MIMO) use several such channels in parallel.

| Technology | Bandwidth $B$ | Carrier | SNR [–] | Note |
|---|---|---|---|---|
| Telephone channel | 3.1 kHz | 300–3400 Hz | 1585 | |
| ADSL | 4.3125 kHz per channel | up to 1.1 MHz | 1000 | 256 parallel channels |
| VDSL | 30 / 35 MHz | up to 35 MHz | 1000 | |
| Wi-Fi 802.11n | 20 / 40 MHz | 2.4 / 5 GHz | 316 / 631 | |
| 5G | 100 MHz | 2.3 GHz | 32 / 100 | |
| 5G mmWave | 500 / 1000 / 2000 MHz | 28 / 38 / 72 GHz | 6.3 | |

Multiple-input multiple-output (MIMO) systems use several antennas at both ends, denoted 2×2, 4×4, up to 64×64, to carry the same number of independent spatial streams over the same bandwidth.

## Exercise

### Preparation

Create the environment and start JupyterLab as described in the [root README](../README.md), then open `qos_01/exercise_01.ipynb`.

```bash
cd qos-01
uv sync
uv run jupyter lab --ip 0.0.0.0
```

The notebook builds an interactive model from `lib/core.py`: a `HarmSignal` with adjustable amplitude, frequency, phase, and bandwidth, and a `NoiseSignal` with adjustable amplitude, displayed with Bokeh plots and Panel widgets.

### Step 1 – Model a signal with noise

Run the notebook up to the interactive dashboard. Vary the signal and noise parameters with the sliders and observe the combined signal. Before implementing anything, estimate qualitatively how the signal-to-noise ratio and the channel capacity should react to each slider.

### Step 2 – Implement the channel metrics

Implement `calc_signal_power` and `calc_channel_capacity` in the notebook using the formulas above, keeping the signatures of the template cell, which the *Calculate* button calls by name. Verify the displayed values against a manual computation for one setting. Only afterwards compare the result with the reference implementation in `lib/core.py`.

### Step 3 – Apply noise to audio

Record or generate a short audio signal, preferably speech. Add Gaussian white noise of increasing variance and listen to the result. Relate the perceived quality to the computed SNR.

### Step 4 – Apply noise to an image

Load `fig/android_gray.jpeg` as a grayscale array, add Gaussian noise of increasing variance, and display the results. The same image is used again in Exercise 04, where the degradation is measured objectively.

## Questions

1. What is the unit in which SNR is commonly expressed, and how does it relate to the linear ratio used in the Shannon–Hartley formula?
2. How does MIMO affect the channel capacity, given that the bandwidth per stream is unchanged?
3. For the telephone channel in the table, what capacity does the formula give, and how does it compare with the 64 kbit/s PCM stream?
4. What happens to a 5 kHz tone sampled at $f_s = 8$ kHz?

## References

1. C. E. Shannon, "A Mathematical Theory of Communication," *Bell System Technical Journal*, vol. 27, pp. 379–423, 623–656, 1948.
2. C. E. Shannon, "Communication in the Presence of Noise," *Proceedings of the IRE*, vol. 37, no. 1, pp. 10–21, 1949.
3. J. G. Proakis and M. Salehi, *Digital Communications*, 5th ed. McGraw-Hill, 2008.
4. ITU-T Recommendation G.711, *Pulse code modulation (PCM) of voice frequencies*, 1988.
5. Wikipedia, "Signal," https://en.wikipedia.org/wiki/Signal.
