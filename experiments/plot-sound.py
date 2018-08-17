#from pylab import*
from scipy.io import wavfile
import matplotlib.pyplot as plt
import numpy as np

# read in a wav file
sampFreq, snd = wavfile.read('440_sine.wav')

# convert our sound array to floating point values ranging from -1 to 1 
snd = snd / (2.**15)

# select and work with only one of the channels from now onwards
s1 = snd[:,0] 

### Plotting the Tone
# A time representation of the sound can be obtained by plotting the pressure values against the time axis. However, we need to create an array containing the time points first:
timeArray = np.arange(0, 5292.0, 1)
print "create timeArray:",timeArray
timeArray = timeArray / sampFreq
timeArray = timeArray * 1000  #scale to milliseconds
print "scaled timeArray:",timeArray


# plot the tone
plt.plot(timeArray, s1, color='k')
plt.ylabel('Amplitude')
plt.xlabel('Time (ms)')
plt.show()

### Plotting the Frequency Content
# useful graphical representation is that of the frequency content, or spectrum of the tone. We can obtain the frequency spectrum of the sound using the fft function, that implements a Fast Fourier Transform algorithm
n = len(s1) 
p = np.fft.fft(s1) # take the fourier transform 

nUniquePts = int(np.ceil((n+1)/2.0))
p = p[0:nUniquePts]
p = abs(p)

p = p / float(n) # scale by the number of points so that
                 # the magnitude does not depend on the length 
                 # of the signal or on its sampling frequency  
p = p**2  # square it to get the power 

# multiply by two (see technical document for details)
# odd nfft excludes Nyquist point
if n % 2 > 0: # we've got odd number of points fft
    p[1:len(p)] = p[1:len(p)] * 2
else:
    p[1:len(p) -1] = p[1:len(p) - 1] * 2 # we've got even number of points fft

freqArray = np.arange(0, nUniquePts, 1.0) * (sampFreq / n);
plt.plot(freqArray/1000, 10*np.log10(p), color='k')
plt.xlabel('Frequency (kHz)')
plt.ylabel('Power (dB)')
plt.show()


