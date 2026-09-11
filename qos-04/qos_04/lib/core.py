import numpy as np
from scipy.signal import convolve2d


# Reference implementations — students implement these first
def mse(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Mean squared error between two images.

    Parameters
    ----------
    img1, img2 : np.ndarray
        Grayscale images of equal shape with values in [0, L].

    Returns
    -------
    float
        Mean of the squared pixel differences [-].
    """
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    return float(np.mean((img1 - img2) ** 2))


def psnr(img1: np.ndarray, img2: np.ndarray, L: int = 255) -> float:
    """
    Peak signal-to-noise ratio between two images.

    Parameters
    ----------
    img1, img2 : np.ndarray
        Grayscale images of equal shape with values in [0, L].
    L : int, optional
        Dynamic range of the pixel values, by default 255 for 8-bit images.

    Returns
    -------
    float
        PSNR [dB]; infinite for identical images.
    """
    error = mse(img1, img2)
    if error == 0:
        return float("inf")
    return 20 * np.log10(L / np.sqrt(error))


# SSIM
def gaussian_kernel(window_size: int = 11, sigma: float = 1.5) -> np.ndarray:
    """
    Normalized 2-D Gaussian window.

    Parameters
    ----------
    window_size : int, optional
        Side of the square window [px], by default 11.
    sigma : float, optional
        Standard deviation of the Gaussian [px], by default 1.5.

    Returns
    -------
    np.ndarray
        Window of shape (window_size, window_size) summing to 1.
    """
    ax = np.arange(-(window_size // 2), window_size // 2 + 1)
    xx, yy = np.meshgrid(ax, ax)
    kernel = np.exp(-(xx**2 + yy**2) / (2 * sigma**2))
    return kernel / kernel.sum()


def _window(window_size: int, window: str) -> np.ndarray:
    if window == "uniform":
        return np.ones((window_size, window_size)) / window_size**2
    if window == "gaussian":
        return gaussian_kernel(window_size)
    raise ValueError("window must be 'uniform' or 'gaussian'")


def ssim_map(
    img1: np.ndarray,
    img2: np.ndarray,
    window_size: int = 11,
    window: str = "uniform",
    K1: float = 0.01,
    K2: float = 0.03,
    L: int = 255,
) -> np.ndarray:
    """
    Local structural similarity of two images, computed by convolution.

    The local means, variances, and covariance are obtained by convolving the
    images, their squares, and their product with the window.

    Parameters
    ----------
    img1, img2 : np.ndarray
        Grayscale images of equal shape with values in [0, L].
    window_size : int, optional
        Side of the sliding window [px], by default 11.
    window : {"uniform", "gaussian"}, optional
        Weighting of the window, by default "uniform".
    K1, K2 : float, optional
        Constants of the stabilizing terms c1 = (K1 L)^2 and c2 = (K2 L)^2.
    L : int, optional
        Dynamic range of the pixel values, by default 255.

    Returns
    -------
    np.ndarray
        SSIM index of every pixel's window [-], same shape as the images.
    """
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    C1 = (K1 * L) ** 2
    C2 = (K2 * L) ** 2
    w = _window(window_size, window)

    conv = lambda x: convolve2d(x, w, mode="same", boundary="symm")  # noqa: E731
    mu1 = conv(img1)
    mu2 = conv(img2)
    sigma1_sq = conv(img1 * img1) - mu1**2
    sigma2_sq = conv(img2 * img2) - mu2**2
    sigma12 = conv(img1 * img2) - mu1 * mu2

    return ((2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)) / (
        (mu1**2 + mu2**2 + C1) * (sigma1_sq + sigma2_sq + C2)
    )


def ssim(img1: np.ndarray, img2: np.ndarray, **kwargs) -> float:
    """
    Structural similarity index: the mean of the SSIM map.

    Parameters
    ----------
    img1, img2 : np.ndarray
        Grayscale images of equal shape with values in [0, L].
    **kwargs
        Passed to :func:`ssim_map`.

    Returns
    -------
    float
        SSIM index [-] in [-1, 1].
    """
    return float(np.mean(ssim_map(img1, img2, **kwargs)))


def ssim_loop(
    img1: np.ndarray,
    img2: np.ndarray,
    window_size: int = 11,
    K1: float = 0.01,
    K2: float = 0.03,
    L: int = 255,
) -> float:
    """
    Structural similarity index computed literally, window by window.

    Equivalent to :func:`ssim` with a uniform window; kept for reference and
    for comparing its running time with the convolution form.

    Parameters
    ----------
    img1, img2 : np.ndarray
        Grayscale images of equal shape with values in [0, L].
    window_size : int, optional
        Side of the sliding window [px], by default 11.
    K1, K2, L
        As in :func:`ssim_map`.

    Returns
    -------
    float
        SSIM index [-].
    """
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    C1 = (K1 * L) ** 2
    C2 = (K2 * L) ** 2
    w = np.ones((window_size, window_size)) / window_size**2

    M, N = img1.shape
    pad = window_size // 2
    # Match convolve2d(boundary="symm"), including the edge pixels.
    p1 = np.pad(img1, pad, mode="symmetric")
    p2 = np.pad(img2, pad, mode="symmetric")

    total = 0.0
    for i in range(M):
        for j in range(N):
            r1 = p1[i : i + window_size, j : j + window_size]
            r2 = p2[i : i + window_size, j : j + window_size]
            mu1 = np.sum(w * r1)
            mu2 = np.sum(w * r2)
            s1 = np.sum(w * (r1 - mu1) ** 2)
            s2 = np.sum(w * (r2 - mu2) ** 2)
            s12 = np.sum(w * (r1 - mu1) * (r2 - mu2))
            total += ((2 * mu1 * mu2 + C1) * (2 * s12 + C2)) / ((mu1**2 + mu2**2 + C1) * (s1 + s2 + C2))
    return total / (M * N)
