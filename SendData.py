"""Example program to demonstrate how to send a multi-channel time series to
LSL."""

import time
from random import random as rand

from pylsl import StreamInfo, StreamOutlet

# first create a new stream info (here we set the name to BioSemi,
# the content-type to EEG, 8 channels, 100 Hz, and float-valued data) The
# last value would be the serial number of the device or some other more or
# less locally unique identifier for the stream as far as available (you
# could also omit it but interrupted connections wouldn't auto-recover)


import scipy
import numpy as np
import pdb

#frequence de simulation
freq = range(35,46)
amplitude = [0.5,1]
samplingRate = 500

#number of channel
chanNum = 64

info = StreamInfo('SimulatedSignal', 'EEG', chanNum, samplingRate, 'float32', 'myuid34234')
# next make an outlet
outlet = StreamOutlet(info)

signalFort = [3,36,7,39]
signalFaible = [37,6,41,2,24]

print("now sending data...")
t=0
while True:
    # make a new random 8-channel sample; this is converted into a
    # pylsl.vectorf (the data type that is expected by push_sample)
    mysample = [np.random.normal(0,0.1) for i in range(64)]
    
    for i in signalFort:
        for ifreq in freq:
           mysample[i]=mysample[i]+2*np.sin(2*np.pi*t*ifreq/samplingRate)
    for i in signalFaible:
        for ifreq in freq:
           mysample[i]=mysample[i]+np.sin(2*np.pi*t*ifreq/samplingRate) 
    #mysample = [amplitude[i]*np.sin(2*np.pi*t*freq[i]/samplingRate)+np.random.normal(0,0.3) for i in range(64)]
    # now send it and wait for a bit
    outlet.push_sample(mysample)
    t=t+1
