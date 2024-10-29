import numpy as np


def linear_to_ulaw(pcm_data):
  """
  Vectorized conversion of 16-bit linear PCM to μ-law
  """
  pcm_data = np.asarray(pcm_data)
  pcm_data = np.clip(pcm_data, -32768, 32767)
  
  # Get sign and magnitude
  sign = (pcm_data < 0).astype(np.uint8)
  abs_pcm = np.abs(pcm_data)
  
  # Add bias
  abs_pcm += 0x84
  
  # Find segment using log2
  seg = np.maximum(0, np.minimum(7, (np.log2(abs_pcm) - 6).astype(int)))
  
  # Calculate mantissa based on segment
  mantissa = (abs_pcm >> (seg + 3)) & 0x0F
  
  # Combine fields
  ulaw = ~((sign << 7) | (seg << 4) | mantissa) & 0xFF
  
  return ulaw.astype(np.uint8)

def linear_to_alaw(pcm_data):
  """
  Vectorized conversion of 16-bit linear PCM to A-law
  """
  pcm_data = np.asarray(pcm_data)
  pcm_data = np.clip(pcm_data, -32768, 32767)
  
  # Get sign and magnitude
  sign = (pcm_data < 0).astype(np.uint8)
  abs_pcm = np.abs(pcm_data)
  
  # Find segment using log2
  seg = np.maximum(0, np.minimum(7, (np.log2(abs_pcm) - 6).astype(int)))
  
  # Calculate mantissa based on segment
  mantissa = (abs_pcm >> (seg + 3)) & 0x0F
  
  # Combine fields and XOR with 0x55
  alaw = ((sign << 7) | (seg << 4) | mantissa) ^ 0x55
  
  return alaw.astype(np.uint8)