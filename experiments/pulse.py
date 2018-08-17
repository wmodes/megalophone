#!/usr/bin/env python

# Refs:
#   https://stackoverflow.com/questions/2648151/python-frequency-detection
#   https://people.csail.mit.edu/hubert/pyaudio/docs/

# On each string, light each LED in sequence, and repeat.

import opc, time
from random import randint

#numLEDs = 512
leds_in_string = 64
total_strings = 4
total_leds = leds_in_string * total_strings
client = opc.Client('localhost:7890')
r_color = randint(0,255)
g_color = randint(0,255)
b_color = randint(0,255)
width_of_pulse = 5   # this should be an odd number
pulse_decay = 0.85
sleeptime = 0.02 #orig 0.01

while True:
    color_string = raw_input("Enter pulse color as triplet (128, 0, 64) OR Enter to use last one: ")
    if color_string <> "":
        color_list = [x.strip() for x in color_string.split(',')]
        (r_color,g_color,b_color) = list(map(int, color_list))
    for led_num in range(leds_in_string):
        # start with all LEDS set to 0,0,0
        pixels = [ (0,0,0) ] * total_leds
        # set the ones we want lit
        for string in range(total_strings):
            index = string * leds_in_string + led_num
            # set center of pulse
            pixels[index] = (r_color, g_color, b_color)
            #print pixels[index],
            # set edges of pulse
            for width_index in range(1,((width_of_pulse-1)/2)+1):
                decay = (1 - pulse_decay) ** width_index
                r_edge_color = int(r_color * decay)
                g_edge_color = int(g_color * decay)
                b_edge_color = int(b_color * decay)
                if (led_num - width_index >= 0):
                    pixels[index - width_index] = (r_edge_color, g_edge_color, b_edge_color)
                    #print pixels[index - width_index],
                if (led_num + width_index < leds_in_string-1):
                    pixels[index + width_index] = (r_edge_color, g_edge_color, b_edge_color)
                    #print pixels[index + width_index],
            #print
        client.put_pixels(pixels)
        time.sleep(sleeptime)
