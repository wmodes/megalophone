import wave
import numpy as np
import pylab as pl

rate, data = wave.open('test-tones/250Hz_44100Hz_16bit_05sec.wav')
t = np.arange(len(data[:,0]))*1.0/rate
pl.plot(t, data[:,0])
pl.show()

p = 20*np.log10(np.abs(np.fft.rfft(data[:2048, 0])))
f = np.linspace(0, rate/2.0, len(p))
pl.plot(f, p)
pl.xlabel("Frequency(Hz)")
pl.ylabel("Power(dB)")
pl.show()
