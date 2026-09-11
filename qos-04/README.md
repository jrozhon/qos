# Exercise 04 – Objective image quality: PSNR and SSIM

This exercise transfers the idea of intrusive quality assessment from speech to images. Two full-reference metrics are examined: the peak signal-to-noise ratio (PSNR), a purely signal-based measure, and the structural similarity index (SSIM), which models properties of human vision. Students implement MSE and PSNR, use a supplied SSIM implementation, and apply both metrics to images degraded by dense and by sparse Gaussian noise, observe where the two metrics disagree, and relate the outcome to their own judgment.

## Learning objectives

- Define mean squared error and PSNR, state their units, and explain their limits as quality indicators.
- Explain the luminance, contrast, and structure terms of SSIM and the role of the stabilizing constants.
- Implement MSE and PSNR in NumPy, and use a supplied SSIM implementation to compare local image structure.
- Compare the behavior of PSNR and SSIM on dense and sparse distortions and explain the differences.
- Place PSNR, SSIM, and VMAF in the wider context of image and video quality assessment.

## Knowledge prerequisites

Students should be able to:

- Calculate means and squared differences, evaluate logarithms, and interpret variance and standard deviation from [Exercises 01](../qos-01/README.md) and [02](../qos-02/README.md).
- Index and slice a two-dimensional NumPy array, perform element-wise arithmetic, and display an array as a grayscale image.
- Explain the distinction between subjective ratings and objective quality estimates from [Exercise 03](../qos-03/README.md).

The image quality metrics and their local image statistics are introduced below. The practical work provides implementations for comparing image windows; prior experience implementing image filters is not required.

## Theory

### Full-reference metrics

As with PESQ and ViSQOL in [Exercise 03](../qos-03/README.md#speech-quality-assessment), the metrics of this exercise are *intrusive* or *full-reference*: they compare a degraded image $K$ with the undistorted original $I$ and return a single number. Both images are grayscale arrays of $m \times n$ pixels with values in $[0, L]$, where $L$ is the maximum allowed pixel value. For unsigned $b$-bit images, $L = 2^b - 1$ ($255$ for 8-bit images); for images normalized to $[0, 1]$, use $L = 1$. Both inputs must use the same scale, shape, and spatial alignment. Convert to floating point before subtraction to avoid unsigned-integer wraparound.

### Mean squared error and PSNR

The mean squared error (MSE) averages the squared pixel differences:

$$
\mathrm{MSE} = \frac{1}{mn} \sum_{i=0}^{m-1} \sum_{j=0}^{n-1} \big[ I(i,j) - K(i,j) \big]^2
$$

where $I(i,j)$ and $K(i,j)$ are the pixel values of the original and the degraded image [–] and $m$, $n$ are the image dimensions [px]. The peak signal-to-noise ratio relates the largest possible signal power to this error and expresses the ratio in decibels:

$$
\mathrm{PSNR} = 10 \log_{10} \frac{L^2}{\mathrm{MSE}} = 20 \log_{10} \frac{L}{\sqrt{\mathrm{MSE}}}
$$

where $L$ is the maximum allowed pixel value [–] and PSNR is in [dB]. Under the stated $[0, L]$ bounds, PSNR is nonnegative and is infinite for identical images. There is no universal PSNR threshold for acceptable quality: perception depends on image content, distortion, and viewing conditions. PSNR weighs squared errors equally regardless of their location or visibility.

For example, pixel arrays $[0, 2]$ and $[0, 4]$ have MSE $2$. With a declared maximum $L = 4$, their PSNR is $10 \log_{10}(16/2) \approx 9.03$ dB. The value of $L$ comes from the chosen representation, not the largest pixel observed in an individual image.

### Structural similarity

The human visual system is sensitive to *structure*, the spatial pattern of intensities. SSIM uses this observation to complement pixel-wise error measures. SSIM compares two image windows $x$ and $y$ through three local statistics: the means $\mu_x$, $\mu_y$ (luminance), the standard deviations $\sigma_x$, $\sigma_y$ (contrast), and the covariance $\sigma_{xy}$ (structure). Covariance describes whether corresponding pixel values rise and fall together relative to their local means. The combined index is

$$
\mathrm{SSIM}(x, y) = \frac{(2 \mu_x \mu_y + c_1)(2 \sigma_{xy} + c_2)}{(\mu_x^2 + \mu_y^2 + c_1)(\sigma_x^2 + \sigma_y^2 + c_2)}
$$

where $c_1 = (k_1 L)^2$ and $c_2 = (k_2 L)^2$ are small constants that stabilize the division when the denominators approach zero, with $k_1 = 0.01$ and $k_2 = 0.03$ by default. The index is dimensionless [–] and lies in $[-1, 1]$; it equals 1 only for identical windows.

SSIM is evaluated over a sliding window. The [original formulation](https://ece.uwaterloo.ca/~z70wang/publications/ssim.pdf) uses an $11 \times 11$ Gaussian window with $\sigma = 1.5$ pixels; this exercise starts with uniform weights to simplify the calculation. The result is an *SSIM map* showing where the images differ structurally; the reported index is its mean. Computing the local means and variances is a convolution of the image (and of its square and the product of the two images) with the window, which is how the supplied implementation proceeds. Both course implementations include a value at every pixel, using symmetric padding that repeats the edge pixel. They use weighted population statistics. Record window size, weights, padding, and $L$ when comparing results with another library, since different conventions can change the score.

### Comparison

| | PSNR | SSIM |
|---|---|---|
| Measures | pixel-wise error energy | local luminance, contrast, and structure |
| Perceptual model | none | sensitivity of human vision to structure |
| Unit and range | dB, $[0, +\infty]$ under the stated pixel bounds | [–], $[-1, 1]$, 1 for identical images |
| Cost | negligible | one convolution per statistic |
| Weakness | treats all errors alike; high values for content that looks poor | misses semantic and high-level effects; sensitive to misalignment |

For video, PSNR and SSIM can be computed per frame and then pooled into a sequence score. State the pooling method: averaging frame PSNR values differs from computing PSNR from the average frame MSE because the logarithm is nonlinear.

**VMAF** (Video Multimethod Assessment Fusion), developed by Netflix, combines several image and motion-related features using a model trained on subjective scores. Its agreement with viewers depends on the selected model, content, distortion, and viewing conditions; it is not uniformly superior to PSNR or SSIM. See the [VMAF project documentation](https://github.com/Netflix/vmaf). VMAF is further context rather than an implementation task in this exercise.

### Test images

`fig/` contains two 1024 × 1024 grayscale originals, `android_gray.png` (a PNG version of the subject used in Exercise 01) and `parrot_gray.png`, and degraded versions of the android image: `noisy_image_var0_01.png`, `noisy_image_var0_05.png`, and `noisy_image_var0_1.png` with Gaussian noise of variance 0.01, 0.05, and 0.1 on a $[0, 1]$ scale applied to every pixel, and `noisy_image_var0_1_mask0.001.png`, `…mask0.01.png`, and `…mask0.1.png` with noise of variance 0.1 applied to a random fraction of 0.1 %, 1 %, and 10 % of the pixels.

The noise variances describe the generated noise before clipping to the image range and saving. Measure MSE from the saved images; it need not equal the nominal noise variance. Use each degraded image with the exact original from which it was generated.

![Original image](fig/android_gray.png)

![Gaussian noise of variance 0.1 on every pixel](fig/noisy_image_var0_1.png)

![Gaussian noise of variance 0.1 on 1 % of the pixels](fig/noisy_image_var0_1_mask0.01.png)

## Exercise

### Preparation

Create the environment and start JupyterLab as described in the [root README](../README.md), then open `qos_04/exercise_04.ipynb`.

```bash
cd qos-04
uv sync
uv run jupyter lab --ip 0.0.0.0
```

`mse()` and `psnr()` are implemented by you in the notebook before the reference versions are imported. `lib/core.py` also provides `ssim()` in two forms, a direct loop over all windows that follows the formula literally (`ssim_loop()`) and a vectorized version using `scipy.signal.convolve2d`, together with `ssim_map()` and `gaussian_kernel()`.

### Step 1 – PSNR of the noisy images

Implement MSE and PSNR, then compute both for the three densely noised images and test whether PSNR falls as the nominal noise variance rises. Add your own degradations from Exercise 01 if you kept them.

### Step 2 – SSIM of the noisy images

Compute SSIM for the same pairs with the vectorized implementation. Time both implementations on the same 256 × 256 crop and verify that their SSIM values agree within floating-point precision before comparing speed. Display the SSIM map of one pair and identify which regions of the image contribute most to the loss of similarity.

### Step 3 – Dense versus sparse noise

Compute PSNR and SSIM for the three masked images. Order the six degraded images by PSNR, by SSIM, and by your own visual judgment, and compare the three orderings. To isolate the effect of spatial concentration, also compare dense and sparse degradations with approximately equal measured MSE. Report any remaining MSE difference; unequal error energy confounds this comparison.

### Step 4 – Window and weighting

Repeat the SSIM computation with the Gaussian window and with window sizes of 7 and 15 pixels. Note how much the index changes, and whether the ordering from Step 3 does.

## Questions

1. Why is PSNR expressed relative to the peak value $L$ rather than to the actual signal power, as SNR was in Exercise 01?
2. Two degraded images have the same MSE and pixel range, but their errors have different spatial patterns. Why must their PSNR values be equal, and why does MSE alone not determine their SSIM values?
3. For two identical flat windows, which term would be undefined without $c_2$? When is $c_1$ also needed, and what value should SSIM have for identical windows?
4. Why can two codec outputs with similar PSNR differ in perceived quality? Give an example of a distortion whose visibility depends on its location or spatial pattern.
5. Why can VMAF correlate better with viewers than SSIM, and why does that not make it a replacement for SSIM in every application?

## References

1. Z. Wang, A. C. Bovik, H. R. Sheikh, and E. P. Simoncelli, "Image Quality Assessment: From Error Visibility to Structural Similarity," *IEEE Transactions on Image Processing*, vol. 13, no. 4, pp. 600–612, 2004.
2. Q. Huynh-Thu and M. Ghanbari, "Scope of validity of PSNR in image/video quality assessment," *Electronics Letters*, vol. 44, no. 13, pp. 800–801, 2008.
3. Z. Li, A. Aaron, I. Katsavounidis, A. Moorthy, and M. Manohara, "Toward A Practical Perceptual Video Quality Metric," Netflix Technology Blog, 2016. Source: https://github.com/Netflix/vmaf.
4. ITU-R Recommendation BT.500, *Methodologies for the subjective assessment of the quality of television images*, 2023.
