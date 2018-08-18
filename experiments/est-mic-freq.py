import pyaudio
import numpy as np
import struct
import audioop
import curses
import math
import time

stdscr = curses.initscr()

CHUNK = 2048
WIDTH = 2
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 60 * 5

SCALE = 40
TOP = 10
LOFREQ = 20
HIFREQ = 1000
LOVOL = 30
HIVOL = 100

local_max_vol_threshold = 50
local_max_timeout = 2   # sec

def main():

    local_max_freq = 0.0
    local_max_vol = 0.0
    local_max_time = 0.0

    stdscr.addstr(TOP + 1, 0, "{0}dB                                 {1}dB".format(LOVOL, HIVOL))
    stdscr.addstr(TOP + 2, 0, "|----|----|----|----|----|----|----|----| Volume")
    stdscr.addstr(TOP + 5, 0, "{0}Hz                                 {1}kHz".format(LOFREQ, HIFREQ/1000))
    stdscr.addstr(TOP + 6, 0, "|----|----|----|----|----|----|----|----| Freq")

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
            vol = 20 * np.log10(rms)
        else:
            vol = 0

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

        # if the last local max was > 5 sec ago, clear it
        if time.time() > local_max_time + local_max_timeout:
            local_max_vol = 0
            local_max_freq = 0
            local_max_time = time.time()

        if (LOVOL < vol < HIVOL):
            # show vol on scale
            #   scale vol for display
            if not math.isnan(vol) and not math.isinf(vol):
                norm_vol = int(SCALE * ((vol - LOVOL) / (HIVOL - LOVOL)))
            else:
                norm_vol = 0
            #   scale lcoal max vol for display
            norm_local_max_vol = int(SCALE * ((local_max_vol - LOVOL) / (HIVOL - LOVOL)))
            #   create scale
            vol_line = " " * SCALE
            vol_list = list(vol_line)
            #   put vol on scale
            vol_list[norm_vol] = '*'
            #   put local max vol on scale
            if norm_local_max_vol <> norm_vol:
                vol_list[norm_local_max_vol] = '|'
            vol_line = ''.join(vol_list)
            stdscr.addstr(TOP + 3, 0, vol_line)

        if (LOFREQ < freq < HIFREQ and LOVOL < vol < HIVOL):
            if not math.isnan(freq) and not math.isinf(freq):
                # calc max and display
                if vol > local_max_vol_threshold and vol > local_max_vol:
                    local_max_vol = vol
                    local_max_freq = freq
                    local_max_time = time.time()
                # show freq on scale
                #   scale freq for display
                norm_freq = int(SCALE * ((freq - LOFREQ) / (HIFREQ - LOFREQ)))
                #   scale local max freq for display
                norm_local_max_freq = int(SCALE * ((local_max_freq - LOFREQ) / (HIFREQ - LOFREQ)))
                #   create scale
                freq_line = " " * SCALE
                freq_list = list(freq_line)
                #   put freq on scale
                freq_list[norm_freq] = '*'
                #   put lcoal max freq on scale
                if norm_local_max_freq <> norm_freq:
                    freq_list[norm_local_max_freq] = '|'
                freq_line = ''.join(freq_list)
                stdscr.addstr(TOP + 7, 0, freq_line)

        stdscr.addstr(TOP + 9, 0, "Max freq: {0:4}Hz Max vol: {1:4}dB".format(
            int(local_max_freq),int(local_max_vol)))

        stdscr.refresh()

    stream.close()
    p.terminate()


try:
    main();
    curses.endwin()                                                                                
except KeyboardInterrupt:            
    curses.endwin()
    exit() 
