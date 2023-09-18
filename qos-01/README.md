# Exercise QoS_1

## Signal:
It is a physical representation of the message, or a mathematical model describing the message.
## Signal classification:
**Continuous (ANALOG)**

 ```A continuous or piecewise continuous function of a continuous independent variable.```
 ![Continuous signal](https://imgur.com/ZjTvG7k.png)

**Discrete signal** 

```Signal discretized in the independent variable (i.e. Df = discrete set of points).```
![Discrete signal](https://imgur.com/3x6mUSb.png)
      
**Digital signal** 

```Signal discretized in independent variable and quantized in level.```
    
     
**Stepped signal** 

```Discretized in Hf, but in parts continuous in time.```
![Stepped signal](https://imgur.com/2V4WWC7.png)

     
**Deterministic signal** 

```At any moment we can determine its value, we have its mathematical description (sin(x, ...)).```

**Stochastic signal**

```We cannot clearly determine their value at any time, probabilistic or statistical methods are used to describe them.```

## PCM (Pulse Coded Modulation):

**Sampling:** 

We select a limited number of samples from the continuous analog signal that represents the recorded sound or image. 
The result is a finite number of analog samples that are captured with a period T_sr given by the sampling rate.


**Quantization:**

This is level discretization (i.e. rounding the actual value to pre-selected values). 
The result of this operation is a finite number of samples (that were already available after sampling) with a finite number of their values, which are expressed by a certain binary code.


**Coding:**

Replace the obtained simple binary code with a code that is more suitable for further processing.

> **TIP:** The sampling circuit introduces error in the form of (overlapping) aliasing, the quantization circuit in the form of quantization noise.
 ###  Conditions for correct sampling (Shannon-Kotelnik theorem):
 
 The sampling theorem applies here, which states that a signal is only describable if it is bounded by a frequency $f_{max}$, and if $f_{sr}$ => 2 * $f_{max}$, i.e. it means that the sampling frequency must be at least twice the highest frequency of the signal.  
 
 Use e.g. for DPS (Digital Signaling Processor) - allows frequency adjustment, volume adjustment, or signal compression. E.g. MP3 - the analogue signal is converted to a digital signal, then to a DSP, which encodes the signal and decodes it back using a DSP (MPEG-1/2 for audio compression).

$T[s]$ (Period) - denotes in physics a physical quantity that indicates the duration of one repetition of a periodic event
$f[Hz = s^{-1}]$ (Frequency or frequency) - indicates the number of periods per unit time

### Gaussian noise:
Gaussian noise represents random changes in intensity corresponding to a Gaussian (normal) distribution.

![Gauss](https://imgur.com/tN6l2ad.png)

$$P(x) = \frac{1}{{\sigma \sqrt {2\pi } }}e^{{{-  {(z - \mu )}^2 } \mathord{/ { {{ - ( {x - \mu }^2 } {2\sigma ^2 }}}} {(2\sigma^2)}}}$$

The standard deviation ($\sigma$), denoted by the Greek letter σ, is a measure of statistical variability often used in probability theory and statistics. 
It is the square root of the variance of a random variable. The sampling standard deviation is a characteristic of the variability (variability) of a statistical population.

![Gauss](https://imgur.com/X1hUPFG.png)

### Channel capacity (Shannon's formula):

**C = B * log_2 (1+ S/N)**

**C:** channel capacity (bps)

**B:** channel bandwidth (Hz)

**S:** signal power

**N:** noise power (W)

**S/N:** signal to noise ratio

### Frequency:
**Telephone channel:**  ```3100 Hz```  (300 - 3400 Hz band)

**WiFi 802.11n:** ```20 MhZ``` (2.4 GHz)/```40 MhZ``` (5 GHz), (band)

**5G:** ```100 MhZ```  (2300 MhZ)

**5G mmWave:** ```500/1000/2000 MhZ``` (28/38/72 GhZ)

**MIMO:** ```800 MhZ``` (band), 2x2, 4x4, 8x8, 16x16, 32x32, and 64x64 (Antennas) - 28/73 GhZ
The numbers refer to the number of streams the router is working with. The router in the 2x2 variant has two antennas that are used for 2 simultaneous streams. 

