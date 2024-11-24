# PSNR (Peak Signal-to-Noise Ratio)

PSNR is a widely used metric in image processing to assess the quality of reconstructed or compressed images. It is defined as the ratio between the maximum possible power of a signal and the power of corrupting noise that affects the fidelity of its representation. Essentially, PSNR compares a degraded image to an original, error-free image, and provides a numerical value that represents the error between the two. The higher the PSNR value, the more similar the degraded image is to the original. However, it's worth noting that while PSNR is easy to compute and widely used, it doesn’t always align well with human-perceived image quality, especially when the distortions are complex or structured in a way that is particularly noticeable to the human eye.

$$
\text{PSNR} = 10 \cdot
\log_{10}\left(\frac{\text{MAX}_I^2}{\text{MSE}}\right)
$$

where MAX<sub>I</sub> is the maximum possible pixel value of the image. When the pixels are represented using 8 bits per sample, this is 255. MSE is the Mean Squared Error between the original and the compressed image, defined as:

$$
\text{MSE} = \frac{1}{mn}\sum_{i=0}^{m-1}\sum_{j=0}^{n-1}[I(i,j) - K(i,j)]^2
$$

## Implementation

```python
import math
import numpy as np

def calculate_psnr(img1, img2):
    # img1 and img2 have range [0, 255]
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    mse = np.mean((img1 - img2)**2)
    if mse == 0:
        return float('inf')
    return 20 * math.log10(255.0 / math.sqrt(mse))
```

# SSIM (Structural Similarity Index)

Unlike PSNR, SSIM on the other hand, is designed to improve upon traditional methods like PSNR by considering image degradation as perceived change in structural information. The SSIM index is calculated on various windows of an image, and the measure between two windows x and y of common size N×N is designed to assess the structural similarity between them. SSIM is based on the
understanding that the human visual system is highly sensitive to structural information in the visual scene, and it takes into consideration luminance, contrast, and structure by comparing local patterns of pixel intensities in the images. SSIM tends to correlate better with the human perception of image quality as it considers structural distortion, luminance distortion, and texture distortion.

The SSIM (Structural Similarity Index) between two windows x and y of common size N×N is:

$$
\text{SSIM}(x, y) = \frac{(2\mu_x\mu_y + c_1)(2\sigma_{xy} + c_2)}{(\mu_x^2 +
\mu_y^2 + c_1)(\sigma_x^2 + \sigma_y^2 + c_2)}
$$

where μ<sub>x</sub> and μ<sub>y</sub> are the average of x and y;
σ<sub>x</sub><sup>2</sup> and σ<sub>y</sub><sup>2</sup> are the variances of x
and y; σ<sub>xy</sub> is the covariance of x and y;
c<sub>1</sub>=(k<sub>1</sub>L)<sup>2</sup>,
c<sub>2</sub>=(k<sub>2</sub>L)<sup>2</sup> are two variables to stabilize the division with weak denominator; L is the dynamic range of the pixel-values (usually this is 2#bits per pixel−1); and k<sub>1</sub>=0.01 and k<sub>2</sub>=0.03 by default.

## Implementation

```python
import math
import numpy as np
import cv2

def ssim(img1, img2):
    C1 = (0.01 * 255)**2
    C2 = (0.03 * 255)**2

    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    kernel = cv2.getGaussianKernel(11, 1.5)
    window = np.outer(kernel, kernel.transpose())

    mu1 = cv2.filter2D(img1, -1, window)[5:-5, 5:-5]  # valid
    mu2 = cv2.filter2D(img2, -1, window)[5:-5, 5:-5]
    mu1_sq = mu1**2
    mu2_sq = mu2**2
    mu1_mu2 = mu1 * mu2
    sigma1_sq = cv2.filter2D(img1**2, -1, window)[5:-5, 5:-5] - mu1_sq
    sigma2_sq = cv2.filter2D(img2**2, -1, window)[5:-5, 5:-5] - mu2_sq
    sigma12 = cv2.filter2D(img1 * img2, -1, window)[5:-5, 5:-5] - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) *
                                                            (sigma1_sq + sigma2_sq + C2))
    return ssim_map.mean()


def calculate_ssim(img1, img2):
    '''calculate SSIM
    the same outputs as MATLAB's
    img1, img2: [0, 255]
    '''
    if not img1.shape == img2.shape:
        raise ValueError('Input images must have the same dimensions.')
    if img1.ndim == 2:
        return ssim(img1, img2)
    elif img1.ndim == 3:
        if img1.shape[2] == 3:
            ssims = []
            for i in range(3):
                ssims.append(ssim(img1, img2))
            return np.array(ssims).mean()
        elif img1.shape[2] == 1:
            return ssim(np.squeeze(img1), np.squeeze(img2))
    else:
        raise ValueError('Wrong input image dimensions.')
```
PSNR (Peak Signal-to-Noise Ratio) and SSIM (Structural Similarity Index) are two different metrics used to evaluate the quality of an image or video. They assess quality in slightly different ways, and their primary distinctions are as follows:

# Measurement Type:

**PSNR:**

PSNR measures the quality of an image or video by evaluating the amount of noise or distortion present. It calculates the ratio of the peak signal power to the power of the noise. In simple terms, it quantifies how much an image or video has deviated from the original in terms of pixel values.

**SSIM:**

SSIM assesses the structural similarity between the reference (original) and distorted (received or processed) images or videos. It considers not only pixel-wise differences but also structural information such as luminance, contrast, and structure.

# Perceptual Consideration:

**PSNR:**

PSNR is a purely mathematical and technical metric. It doesn't consider human perception of image or video quality. A higher PSNR value indicates less distortion, but it may not correlate well with what humans perceive as better quality.

**SSIM:**

SSIM takes into account the human visual system's characteristics. It considers aspects like luminance, contrast, and structural information that align more closely with human perception. Consequently, a higher SSIM value is often associated with higher perceptual quality.

# Sensitivity to Compression and Artifacts:

**PSNR:**

PSNR is sensitive to compression artifacts. It can sometimes produce high values for heavily compressed content that may not look good to human viewers.

**SSIM:**

SSIM is more robust in assessing compression and other types of distortions. It often provides a better reflection of perceived quality in these scenarios.

# Scale and Range:

**PSNR:**

PSNR is typically measured in decibels (dB), and higher values indicate better quality. A common range is 20-50 dB.

**SSIM:**

SSIM values range from -1 to 1, with 1 indicating perfect similarity. A value of 1 suggests that the reference and distorted images are identical.

# Summary (TLDR;):

**PSNR (Peak Signal-to-Noise Ratio)** is a metric used to measure the quality of reconstructed images or videos compared to their original versions after compression or transmission. It calculates the logarithmic ratio between the maximum possible power of a signal and the power of distorting noise that affects its representation. PSNR is straightforward and widely used because it's easy to compute and offers a basic indication of quality loss. However, its major weakness is that it doesn't align well with human visual perception; it treats all errors equally without considering how noticeable they are to the human eye. This means that high PSNR values don't always correspond to perceived high-quality visuals, limiting its effectiveness in evaluating compression algorithms that exploit human perception.

**SSIM (Structural Similarity Index Measure)** is a method for assessing image and video quality by comparing the structural information between the original and a distorted version. It considers factors like luminance, contrast, and texture to model perceived changes in structural information, aiming to reflect the way humans perceive visual content. SSIM's strength lies in its ability to provide a better correlation with human subjective judgment of image quality than traditional metrics like PSNR. It focuses on changes that are structurally significant to human observers. However, SSIM isn't without weaknesses; it can still miss some aspects of visual perception, especially in complex images where high-level semantics or context play a significant role. Additionally, it can be more computationally intensive than simpler metrics.

**VMAF (Video Multimethod Assessment Fusion)** is a sophisticated video quality assessment tool developed by Netflix that combines multiple quality metrics using machine learning to predict perceived video quality. It integrates different aspects of visual perception, including spatial and temporal features, to model how viewers perceive video quality realistically. The strength of VMAF lies in its high correlation with human subjective assessments, making it a powerful tool for optimizing video encoding and streaming to enhance viewer experience. However, VMAF's complexity can be a weakness; it requires significant computational resources and may not be suitable for real-time applications or scenarios with limited processing power. Additionally, because it is trained on specific datasets, its predictions might be less accurate for content types or viewing conditions that differ significantly from those used in its development.