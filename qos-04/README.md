# Exercise 04 – Objective image quality: PSNR and SSIM

This exercise transfers the idea of intrusive quality assessment from speech to images. Two full-reference metrics are derived and implemented: the peak signal-to-noise ratio (PSNR), a purely signal-based measure, and the structural similarity index (SSIM), which models properties of human vision. Students apply both to images degraded by dense and by sparse Gaussian noise, observe where the two metrics disagree, and relate the outcome to their own judgment.

## Learning objectives

- Define the mean squared error and the PSNR of a degraded image and state their units and typical ranges.
- Explain the luminance, contrast, and structure terms of SSIM and the role of the stabilizing constants.
- Implement both metrics in NumPy, including SSIM by local windowing with convolution.
- Compare the behavior of PSNR and SSIM on dense and sparse distortions and explain the differences.
- Place PSNR, SSIM, and VMAF in the wider context of image and video quality assessment.

## Theory

### Full-reference metrics

As with PESQ and ViSQOL in [Exercise 03](../qos-03/README.md#speech-quality-assessment), the metrics of this exercise are *intrusive* or *full-reference*: they compare a degraded image $K$ with the undistorted original $I$ and return a single number. Both images are grayscale arrays of $m \times n$ pixels with values in $[0, L]$, where $L = 2^b - 1$ is the dynamic range for $b$ bits per pixel ($L = 255$ for 8-bit images).

### Mean squared error and PSNR

The mean squared error (MSE) averages the squared pixel differences:

$$
\mathrm{MSE} = \frac{1}{mn} \sum_{i=0}^{m-1} \sum_{j=0}^{n-1} \big[ I(i,j) - K(i,j) \big]^2
$$

where $I(i,j)$ and $K(i,j)$ are the pixel values of the original and the degraded image [–] and $m$, $n$ are the image dimensions [px]. The peak signal-to-noise ratio relates the largest possible signal power to this error and expresses the ratio in decibels:

$$
\mathrm{PSNR} = 10 \log_{10} \frac{L^2}{\mathrm{MSE}} = 20 \log_{10} \frac{L}{\sqrt{\mathrm{MSE}}}
$$

where $L$ is the dynamic range [–] and PSNR is in [dB]. Identical images have infinite PSNR; values of 30–50 dB are typical for lossy compression, and below about 20 dB the degradation is severe. PSNR is cheap to compute and universally reported, but it weighs every pixel error equally regardless of where it lies or how visible it is, and therefore correlates only loosely with perceived quality.

### Structural similarity

The human visual system is sensitive to *structure*, the spatial pattern of intensities, rather than to absolute pixel errors. SSIM compares two image windows $x$ and $y$ through three local statistics: the means $\mu_x$, $\mu_y$ (luminance), the standard deviations $\sigma_x$, $\sigma_y$ (contrast), and the covariance $\sigma_{xy}$ (structure). The combined index is

$$
\mathrm{SSIM}(x, y) = \frac{(2 \mu_x \mu_y + c_1)(2 \sigma_{xy} + c_2)}{(\mu_x^2 + \mu_y^2 + c_1)(\sigma_x^2 + \sigma_y^2 + c_2)}
$$

where $c_1 = (k_1 L)^2$ and $c_2 = (k_2 L)^2$ are small constants that stabilize the division when the denominators approach zero, with $k_1 = 0.01$ and $k_2 = 0.03$ by default. The index is dimensionless [–] and lies in $[-1, 1]$; it equals 1 only for identical windows.

SSIM is evaluated over a sliding window, typically $11 \times 11$ pixels, either uniform or weighted by a Gaussian with $\sigma = 1.5$. The result is an *SSIM map* showing where the images differ structurally; the reported index is its mean. Computing the local means and variances is a convolution of the image (and of its square and the product of the two images) with the window, which is how the implementation in the notebook proceeds.

### Comparison

| | PSNR | SSIM |
|---|---|---|
| Measures | pixel-wise error energy | local luminance, contrast, and structure |
| Perceptual model | none | sensitivity of human vision to structure |
| Unit and range | dB, typically 20–50 | [–], $[-1, 1]$, 1 for identical images |
| Cost | negligible | one convolution per statistic |
| Weakness | treats all errors alike; high values for content that looks poor | misses semantic and high-level effects; sensitive to misalignment |

For video, both metrics are computed per frame and averaged. **VMAF** (Video Multimethod Assessment Fusion), developed by Netflix, fuses several elementary spatial and temporal metrics with a machine-learned model trained on subjective scores and correlates with viewer ratings substantially better than either PSNR or SSIM, at the cost of a large computational effort and of being tied to the content and viewing conditions it was trained on.

### Test images

`fig/` contains two 1024 × 1024 grayscale originals, `android_gray.png` (the image used in Exercise 01) and `parrot_gray.png`, and degraded versions of the android image: `noisy_image_var0_01.png`, `noisy_image_var0_05.png`, and `noisy_image_var0_1.png` with Gaussian noise of variance 0.01, 0.05, and 0.1 on a $[0, 1]$ scale applied to every pixel, and `noisy_image_var0_1_mask0.001.png`, `…mask0.01.png`, and `…mask0.1.png` with noise of variance 0.1 applied to a random fraction of 0.1 %, 1 %, and 10 % of the pixels.

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

Implement MSE and PSNR, then compute both for the three densely noised images and confirm that PSNR falls as the noise variance rises. Add your own degradations from Exercise 01 if you kept them.

### Step 2 – SSIM of the noisy images

Compute SSIM for the same pairs with the vectorized implementation. Time both implementations on one pair to see why the convolution form is used. Display the SSIM map of one pair and identify which regions of the image contribute most to the loss of similarity.

### Step 3 – Dense versus sparse noise

Compute PSNR and SSIM for the three masked images. Order the six degraded images by PSNR, by SSIM, and by your own visual judgment, and compare the three orderings.

### Step 4 – Window and weighting

Repeat the SSIM computation with the Gaussian window and with window sizes of 7 and 15 pixels. Note how much the index changes, and whether the ordering from Step 3 does.

## Questions

1. Why is PSNR expressed relative to the peak value $L$ rather than to the actual signal power, as SNR was in Exercise 01?
2. Two degraded images have the same MSE, one with noise spread over every pixel and one with the same error energy concentrated in a few pixels. What does PSNR report for each, and what does SSIM report?
3. What happens to the SSIM formula in a flat region of the image where $\mu_x = \mu_y$ and $\sigma_x = \sigma_y = 0$, and how do $c_1$ and $c_2$ prevent it?
4. A video codec is tuned to maximize PSNR. Which kinds of artifacts will it tolerate that a viewer would not?
5. Why can VMAF correlate better with viewers than SSIM, and why does that not make it a replacement for SSIM in every application?

## References

1. Z. Wang, A. C. Bovik, H. R. Sheikh, and E. P. Simoncelli, "Image Quality Assessment: From Error Visibility to Structural Similarity," *IEEE Transactions on Image Processing*, vol. 13, no. 4, pp. 600–612, 2004.
2. Q. Huynh-Thu and M. Ghanbari, "Scope of validity of PSNR in image/video quality assessment," *Electronics Letters*, vol. 44, no. 13, pp. 800–801, 2008.
3. Z. Li, A. Aaron, I. Katsavounidis, A. Moorthy, and M. Manohara, "Toward A Practical Perceptual Video Quality Metric," Netflix Technology Blog, 2016. Source: https://github.com/Netflix/vmaf.
4. ITU-R Recommendation BT.500, *Methodologies for the subjective assessment of the quality of television images*, 2023.
