# general constants
leds_in_string = 64
total_strings = 4
total_leds = leds_in_string * total_strings
sleeptime = 0.0001 #orig 0.01

# pulse constants
width_of_pulse = 3   # this should be an odd number
pulse_decay = 0.90
pulse_bkgd_color = (32,32,32)

# idle constants
minbright = 16   # orig 1.25
maxbright = 128  # orig 255
idle_incr = 0.075 # orig 0.4

# sampling constants
sample_chunk = 1028
sample_width = 2
sample_channels = 1
sample_rate = 44100
sample_sec = 0.05

# sound constants
volume_threshold = 60
lo_freq = 100
hi_freq = 800

# color constants
# blue > green > red
#color_map = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]
# red > orange > yellow > white
#color_map = [(255,0,0), (255,128,0), (255,255,0), (255,255,255)]  
# green > g-y > yellow > orange > red > violet > blue
color_map = [(0,255,0), (128,255,0), (255,255,0), (255,128,0), (255,0,0), (128,0,128), (0,0,255)] 
