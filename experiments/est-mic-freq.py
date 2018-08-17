import pyaudio
import numpy as np
import struct
import audioop
import curses
import math

stdscr = curses.initscr()

CHUNK = 2048
WIDTH = 2
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 60

SCALE = 40
TOP = 10
LOFREQ = 20
HIFREQ = 1000
LOVOL = 30
HIVOL = 100

def main():

    stdscr.addstr(TOP + 1, 0, "{0}Hz                                 {1}kHz".format(LOFREQ, HIFREQ/1000))
    stdscr.addstr(TOP + 2, 0, "|----|----|----|----|----|----|----|----| Freq")
    stdscr.addstr(TOP + 5, 0, "{0}dB                                 {1}dB".format(LOVOL, HIVOL))
    stdscr.addstr(TOP + 6, 0, "|----|----|----|----|----|----|----|----| Volume")

    p = pyaudio.PyAudio()

    # use a Blackman window
    window = np.blackman(CHUNK)

    stream = p.open(format=p.get_format_from_width(WIDTH),
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    output=True,
                    frames_per_buffer=CHUNK)

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK, exception_on_overflow = False)
        #stream.write(data, CHUNK)
        #print "first","%dh"%(len(data)/WIDTH)
        #print "second",data
        #print "third",struct.unpack("%dh"%(len(data)/WIDTH), data)
        #print "fourth",np.array(struct.unpack("%dh"%(len(data)/WIDTH), data))
        #print "fifth",np.array(struct.unpack("%dh"%(len(data)/WIDTH), data))*window

        # get the volume
        rms = audioop.rms(data, 2)
        if (rms > 0):
            decibel = 20 * np.log10(rms)
        else:
            decibel = 0

        # unpack the data and times by the hamming window
        indata = np.array(struct.unpack("%dh"%(len(data)/WIDTH), data))*window
        # Take the fft and square each value
        fftData=abs(np.fft.rfft(indata))**2
        # find the maximum
        which = fftData[1:].argmax() + 1
        # use quadratic interpolation around the max
        if which != len(fftData)-1:
            y0,y1,y2 = np.log(fftData[which-1:which+2:])
            x1 = (y2 - y0) * .5 / (2 * y1 - y2 - y0)
            # find the frequency and output it
            freq = (which+x1)*RATE/CHUNK
        else:
            freq = which*RATE/CHUNK

        #print ("The freq is %f Hz, volume is %f db.      " % (freq, decibel))
        if (LOFREQ < freq < HIFREQ and LOVOL < decibel < HIVOL):
            if not math.isnan(freq) and not math.isinf(freq):
                norm_freq = int(SCALE * ((freq - LOFREQ) / (HIFREQ - LOFREQ)))
                freq_line = (" " * (norm_freq)) + "*" + (" " * (SCALE-norm_freq)) + "%8.0f Hz " % (freq)
                stdscr.addstr(TOP + 3, 0, freq_line)

        if (LOVOL < decibel < HIVOL):
            if not math.isnan(decibel) and not math.isinf(decibel):
                norm_vol = int(SCALE * ((decibel - LOVOL) / (HIVOL - LOVOL)))
        else:
            norm_vol = 0
        vol_line = (" " * (norm_vol)) + "*" + (" " * (SCALE-norm_vol)) + "%8.0f dB " % (decibel)
        stdscr.addstr(TOP + 7, 0, vol_line)

        stdscr.refresh()

    stream.close()
    p.terminate()


try:
    main();
    curses.endwin()                                                                                
except KeyboardInterrupt:            
    curses.endwin()
    exit() 
