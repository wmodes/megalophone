#!/usr/bin/env python

# Burn-in test: Keep LEDs at full brightness most of the time, but dim periodically
# so it's clear when there's a problem.

import opc, time, math

numLEDs = 512
client = opc.Client('localhost:7890')
minbright = 8   # orig 1.25
maxbright = 128  # orig 255
sleeptime = 0.05    # orig 0.05
increment = 0.075 # orig 0.4

t = 0

while True:
    t += increment
    # brightness = int(min(1, 1.25 + math.sin(t)) * maxbright)
    brightness = int(minbright + ((1 + math.sin(t))/2) * (maxbright-minbright))
    #print "t =",t,"(1+sin(t))/2 =",(1+math.sin(t))/2,"brightness =",brightness
    frame = [ (brightness, brightness, brightness) ] * numLEDs
    client.put_pixels(frame)
    time.sleep(sleeptime) 
