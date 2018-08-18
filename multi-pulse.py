#!/usr/bin/env python -u 

# Refs:
#   https://stackoverflow.com/questions/2648151/python-frequency-detection
#   https://people.csail.mit.edu/hubert/pyaudio/docs/

# On each string, light each LED in sequence, and repeat.

# visual includes
import sys
import select
import opc, time
from random import randint
import math
from ast import literal_eval
# audio includes
import pyaudio
import numpy as np
import struct
import audioop
import curses
import math
import time

client = opc.Client('localhost:7890')

#start_color = (randint(0,255), randint(0,255), randint(0,255))
start_color = (255,128,0)

# files monitored for input
read_list = [sys.stdin]

# general constants
leds_in_string = 64
total_strings = 4
total_leds = leds_in_string * total_strings
sleeptime = 0.02 #orig 0.01

# pulse constants
width_of_pulse = 5   # this should be an odd number
pulse_decay = 0.75
pulse_bkgd_color = (32,32,32)

# idle constants
minbright = 16   # orig 1.25
maxbright = 128  # orig 255
idle_incr = 0.075 # orig 0.4

# sampling constants
CHUNK = 2048
WIDTH = 2
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 0.05

# sound constants
SCALE = 40
TOP = 10
LOFREQ = 100
HIFREQ = 800
LOVOL = 30
HIVOL = 100
volume_threshold = 55
lo_freq = 100
hi_freq = 800

# color constants
#color_map = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]  # [BLUE, GREEN, RED]
color_map = [(255,0,0), (255,128,0), (255,255,0), (255,255,255)]  # red, orange, yellow, white

class Field(object):
    """FadeCandy field with idle and pulse functions"""
    def __init__(self):
        self._pulses = []
        self._pixels = []
        self._idle_marker = 0

    def _set_pixel(self, led_index, color):
        if (0 <= led_index <= leds_in_string-1):
            for string in range(total_strings):
                index = string * leds_in_string + led_index
                self._pixels[index] = color

    def _set_field(self, color):
        self._pixels = [ color ] * total_leds

    def _dim_color(self, color, decay):
        (r,g, b) = color
        return (r * decay, g * decay, b * decay)

    def add_pulse(self, color):
        self._pulses.append({
                'index' : 0,
                'color' : color
            })

    def _incr_pulses(self):
        new_list = []
        for pulse_index in range(len(self._pulses)):
            if self._pulses[pulse_index]['index'] < leds_in_string-1:
                self._pulses[pulse_index]['index'] += 1
                # we build a new list
                new_list.append(self._pulses[pulse_index])
                # note that if the index doesn't meet the above
                # condtion, i.e., it is at end, we do not move it
                # to the new list
        self._pulses = new_list
                

    def _pulse_pattern(self):
        # start with all LEDS in field set to 0,0,0
        self._set_field(pulse_bkgd_color)
        # add each pulse to field
        for pulse_index in range(len(self._pulses)):
            led_index = self._pulses[pulse_index]['index']
            led_color = self._pulses[pulse_index]['color']
            # set center of pulse
            self._set_pixel(led_index, led_color)
            # set edges of pulse
            for width_index in range(1,((width_of_pulse-1)/2)+1):
                decay = (1 - pulse_decay) ** width_index
                dim_color = self._dim_color(led_color, decay)
                if (led_index - width_index >= 0):
                    self._set_pixel(led_index - width_index, dim_color)
                if (led_index + width_index < leds_in_string-1):
                    self._set_pixel(led_index + width_index, dim_color)
        self._incr_pulses()

    def _idle_pattern(self):
        t = self._idle_marker
        self._idle_marker += idle_incr
        b = int(minbright + ((1 + math.sin(t))/2) * (maxbright-minbright))
        self._set_field((b,b,b))

    def light_field(self):
        client.put_pixels(self._pixels)

    def run_field(self):
        #while len(self._pulses):
        #while True:
        if len(self._pulses):
            self._pulse_pattern()
        else:
            self._idle_pattern()
        self.light_field()
        time.sleep(sleeptime)

    def convert_to_rgb(self, minval, maxval, val, colors):
        # https://stackoverflow.com/questions/20792445/calculate-rgb-value-for-a-range-of-values-to-create-heat-map
        # colors specifies a series of points deliniating color ranges
        # make sure val is within range
        if val > maxval:
            val = maxval
        if val < minval:
            val = minval
        EPSILON = sys.float_info.epsilon  # smallest possible difference
        # determine where val falls within the entire range
        fi = float(val-minval) / float(maxval-minval) * (len(colors)-1)
        # determine between which color points val falls
        i = int(fi)
        # determine where val falls within that range
        f = fi - i
        # does it fall on one of the color points?
        if f < EPSILON:
            return colors[i]
        else:
            # otherwise return the color within the range it corresponds
            (r1, g1, b1), (r2, g2, b2) = colors[i], colors[i+1]
            return int(r1 + f*(r2-r1)), int(g1 + f*(g2-g1)), int(b1 + f*(b2-b1)) 


class Audio(object):
    """Audio object to receive input and convert to colors"""
    def __init__(self):
        # create a pyaudio object
        self.p = pyaudio.PyAudio()
        # use a Blackman window
        self.window = np.blackman(CHUNK)
        # open a stream to audio in
        self.stream = self.p.open(format=self.p.get_format_from_width(WIDTH),
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        output=True,
                        frames_per_buffer=CHUNK)

    def terminate(self):
        self.stream.close()
        self.p.terminate()

    def estimate_freq_vol(self):
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = self.stream.read(CHUNK, exception_on_overflow = False)
            # get the volume
            rms = audioop.rms(data, 2)
            # convert to decibels
            if (rms > 0):
                vol = 20 * np.log10(rms)
            else:
                vol = 0
            # unpack the data and times by the hamming window
            indata = np.array(struct.unpack("%dh"%(len(data)/WIDTH), data))*self.window
            # Take the fft and square each value
            fftData=abs(np.fft.rfft(indata))**2
            # find the maximum
            which = fftData[1:].argmax() + 1
            # use quadratic interpolation around the max
            if which and which != len(fftData)-1:
                y0,y1,y2 = np.log(fftData[which-1:which+2:])
                x1 = (y2 - y0) * .5 / (2 * y1 - y2 - y0)
                # find the frequency and output it
                freq = (which+x1)*RATE/CHUNK
            else:
                freq = which*RATE/CHUNK
        return((freq,vol))
  


def main_loop():
    global read_list

    vol = 0
    freq = randint(lo_freq, hi_freq)

    print "Enter frequency ({0}-{1}) or press Return to use {2}Hz".\
            format(lo_freq, hi_freq, int(freq))
    # while still waiting for input on at least one file
    while read_list:
        ready = select.select(read_list, [], [], sleeptime)[0]
        if ready:
            for file in ready:
                line = file.readline()
                if not line: # EOF, remove file from input list
                    read_list.remove(file)
                #elif line.rstrip(): # optional: skipping empty lines
                else:
                    if line.rstrip():
                        freq = int(literal_eval(line))
                    else:
                        freq = randint(lo_freq, hi_freq)
                vol = volume_threshold
            print "Enter frequency ({0}-{1}) or press Return to use {2}Hz".\
                    format(lo_freq, hi_freq, int(freq))
        else:
            # print "estimating vol & freq from audio in"
            (freq, vol) = audio.estimate_freq_vol()
        if (vol >= volume_threshold):
            color = field.convert_to_rgb(lo_freq, hi_freq, freq, color_map)
            print "vol:", vol, "freq:", freq, "color:", color
            field.add_pulse(color)
            vol = 0
        field.run_field()

# instantiate objects
field = Field()
audio = Audio()

try:
    main_loop()
except KeyboardInterrupt:
    audio.terminate()
