import numpy as np

def freqBandsPower(data, samplingRate = 500, eeg_bands = {'Delta': (0, 4), 'Theta': (4, 8), 'Alpha': (8, 12), 'Beta': (12, 30), 'Gamma': (30, 45)}):
    """ 
    Computes the power of the signal in the provided frequency bands
    data should be a numpy array, samplingRate is in Hz, and eeg_bands
    is a dict such as {'Delta': (0, 4), 'Theta': (4, 8), 'Alpha': (8, 12), 'Beta': (12, 30), 'Gamma': (30, 45)}
    """
    from scipy.signal import welch
    f, psd = welch(data, fs=1. / samplingRate)
    power = {band: np.mean(psd[np.where((f >= lf) & (f <= hf))]) for band, (lf, hf) in eeg_bands.items()}
    return power
