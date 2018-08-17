#!/usr/bin/env python -u 

# Refs:
#   https://stackoverflow.com/questions/2648151/python-frequency-detection
#   https://people.csail.mit.edu/hubert/pyaudio/docs/

# On each string, light each LED in sequence, and repeat.

import sys
import select
import opc, time
from random import randint
import math
from ast import literal_eval

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
#sleeptime = 0.05    # orig 0.05
idle_incr = 0.075 # orig 0.4

class Field(object):
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


field = Field()

def main_loop():
    global read_list
    
    color = start_color
    print "Enter pulse color as triplet or press Return to use",color,
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
                        color = tuple(literal_eval(line))
                    else:
                        color = (randint(0,255), randint(0,255), randint(0,255))
                    print "Color:",color
                    field.add_pulse(color)
                    print "Enter pulse color as triplet (128, 0, 64) OR Enter to use last one: ",
        field.run_field()

try:
    main_loop()
except KeyboardInterrupt:
    pass
