# PSNR (Peak Signal-to-Noise Ratio)

PSNR is a widely used metric in image processing to assess the quality of
reconstructed or compressed images. It is defined as the ratio between the
maximum possible power of a signal and the power of corrupting noise that
affects the fidelity of its representation. Essentially, PSNR compares a
degraded image to an original, error-free image, and provides a numerical value
that represents the error between the two. The higher the PSNR value, the more
similar the degraded image is to the original. However, it's worth noting that
while PSNR is easy to compute and widely used, it doesn’t always align well with
human-perceived image quality, especially when the distortions are complex or
structured in a way that is particularly noticeable to the human eye.

$$
\text{PSNR} = 10 \cdot
\log_{10}\left(\frac{\text{MAX}_I^2}{\text{MSE}}\right)
$$

where MAX<sub>I</sub> is the maximum possible pixel value of the image. When the
pixels are represented using 8 bits per sample, this is 255. MSE is the Mean
Squared Error between the original and the compressed image, defined as:

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

Unlike PSNR, SSIM on the other hand, is designed to improve upon traditional
methods like PSNR by considering image degradation as perceived change in
structural information. The SSIM index is calculated on various windows of an
image, and the measure between two windows x and y of common size N×N is
designed to assess the structural similarity between them. SSIM is based on the
understanding that the human visual system is highly sensitive to structural
information in the visual scene, and it takes into consideration luminance,
contrast, and structure by comparing local patterns of pixel intensities in the
images. SSIM tends to correlate better with the human perception of image
quality as it considers structural distortion, luminance distortion, and texture
distortion.

$$
\text{SSIM}(x, y) = \frac{(2\mu_x\mu_y + c_1)(2\sigma_{xy} + c_2)}{(\mu_x^2 +
\mu_y^2 + c_1)(\sigma_x^2 + \sigma_y^2 + c_2)}
$$

The SSIM (Structural Similarity Index) between two windows x and y of common
size N×N is:

$$
\text{SSIM}(x, y) = \frac{(2\mu_x\mu_y + c_1)(2\sigma_{xy} + c_2)}{(\mu_x^2 +
\mu_y^2 + c_1)(\sigma_x^2 + \sigma_y^2 + c_2)}
$$

where μ<sub>x</sub> and μ<sub>y</sub> are the average of x and y;
σ<sub>x</sub><sup>2</sup> and σ<sub>y</sub><sup>2</sup> are the variances of x
and y; σ<sub>xy</sub> is the covariance of x and y;
c<sub>1</sub>=(k<sub>1</sub>L)<sup>2</sup>,
c<sub>2</sub>=(k<sub>2</sub>L)<sup>2</sup> are two variables to stabilize the
division with weak denominator; L is the dynamic range of the pixel-values
(usually this is 2#bits per pixel−1); and k<sub>1</sub>=0.01 and
k<sub>2</sub>=0.03 by default.

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
