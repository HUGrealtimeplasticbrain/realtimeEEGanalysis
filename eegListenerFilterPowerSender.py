# Class that allows to listen to an LSL EEG stream, filter it 
#  and compute the power in frequency bands and send it to back through LSL


from pylsl import StreamInlet, resolve_byprop
import numpy as np
import bandPower1
import bandPower2

class EegListenerFilterPowerSender:
    
    def __init__(self, lslInputType = "EEG", lslOutputType = "POWER", outputRate = 20, bufferSize = 250, freqBand = 'Alpha'):
        self.bufferSize = bufferSize
        self.outputRate = outputRate
        self.freqBand = freqBand
        self.lslInputType = lslInputType
        self.stream = self.findStream()
        if self.stream is None:
            return
        self.inputRate = self.stream.nominal_srate()
        self.channels = self.stream.channel_count()
        self.buff = np.zeros((self.bufferSize, self.channels))
        # first create a new stream info (here we set the name to BioSemi, the content-type to EEG, 8 channels, 100 Hz, and float-valued data)
        # The last value would be the serial number of the device or some other more or less locally unique identifier for the stream as far as available (you could also omit it but interrupted connections wouldn't auto-recover).
        self.outputInfo = pylsl.stream_info('EEGpower','Power',self.channels,self.outputRate,pylsl.cf_float32,'PowerAnalyzer');

        
    def startReadAndProcess():
        if self.stream is None:
            print("No stream to read... aborting")
            return
        # create a new inlet to read from the stream
        self.inlet = StreamInlet(self.stream)
        self.outlet = pylsl.stream_outlet(self.outputInfo)
        mustStop = false
        outputEveryNSample = self.inputRate/self.outputRate
        samp = 0
        while not mustStop:
            samp += 1
            np.roll(self.buff, -1, 0)
            self.buff[self.buffSize - 1, :], timestamp = self.inlet.pull_sample()
            if samp % outputEveryNSample == 0:
                self.sendLSL(self.processBuffer())
                self.outlet.push_sample(pylsl.vectorf(self.processBuffer(self.freqBand)))
                
        self.inlet = None       
        
        
    def findStream(self):
        # Search for a stream
        streams = resolve_byprop('type', self.lslInputType, timeout=5.0)
        if len(streams) < 1:
            print("Could not find an EEG stream !")
            return None
        else:
            print("Found EEG stream")
            return streams[0]
        
    def processBuffer(self, band = "Alpha"):
        return bandPower1.freqBandsPower(self.buffer, self.inputRate)[band]
        
        
if __name__ == "__main__":
    worker = EegListenerFilterPowerSender()
    
