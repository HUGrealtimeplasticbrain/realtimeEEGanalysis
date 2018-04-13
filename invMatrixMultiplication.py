
#multiply eeg signal by inv matrix

#read inv matrix
import scipy.io
import scipy.signal
import numpy as np
import pdb
import matplotlib.pyplot as plt
"""Example program to show how to read a multi-channel time series from LSL."""

from pylsl import StreamInlet, resolve_stream, resolve_byprop


invMat = scipy.io.loadmat('/home/neuropsynov/hugHackathon/MNI_actiCHamp64.mat')


# first resolve an EEG stream on the lab network
print("looking for an EEG stream...")
streams = resolve_byprop('type', 'EEG',timeout=5.0)

# create a new inlet to read from the stream
inlet = StreamInlet(streams[0])

nyq=0.5*streams[0].nominal_srate()
low = 1 / nyq
high = 81 / nyq
paramFil = scipy.signal.butter(6, [low, high], btype='band')
#b,a = signal.butter()


currentIndex=0
buffSize=500
buff = np.zeros([buffSize, streams[0].channel_count()])
updateDisplay=0.05 #50ms
nbSampleUpdateDisplay=updateDisplay*streams[0].nominal_srate()
convMatrix=np.ones([nbSampleUpdateDisplay,streams[0].channel_count()])/nbSampleUpdateDisplay

while True:
    # get a new sample (you can also omit the timestamp part if you're not
    # interested in it)
    #sample, timestamp = inlet.pull_sample()
    np.roll(buff, -1, 0)
    buff[buffSize - 1, :], timestamp = inlet.pull_sample()
    #pdb.set_trace()
    filtSample = scipy.signal.filtfilt(paramFil[0],paramFil[1],buff,method="gust",axis=0)
    
    #
    #scipy.signal.filtfilt()
    moySample=scipy.signal.fftconvolve(filtSample,convMatrix,"same")
    invsolmat = np.sqrt(np.multiply(np.dot(invMat["x"],filtSample),np.dot(invMat["x"],filtSample)) + np.multiply(np.dot(invMat["y"],filtSample),np.dot(invMat["y"],filtSample)) + np.multiply(np.dot(invMat["z"],filtSample),np.dot(invMat["z"],filtSample)))
    currentIndex += 1
    if currentIndex % 500 == 0:
       plt.plot(filtSample[:,5], 'b-')
       plt.plot(buff[:,5], 'r-')
       plt.show()

