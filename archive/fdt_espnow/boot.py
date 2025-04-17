# boot.py -- run on boot-up
import sys
from machine import Pin
from neopixel import NeoPixel

pin = Pin(8, Pin.OUT)   # set GPIO0 to output to drive NeoPixels
np = NeoPixel(pin, 8)   # create NeoPixel driver on GPIO0 for 8 pixels
np[0] = (20, 0, 0) # set the first pixel to white
np.write()


global node_mode
node_mode = None

while not node_mode:
    rx = sys.stdin.readline().rstrip()
    print(rx)
    print(type(rx))
    if rx=='gateway':
        node_mode = 'gateway'
        break
    elif rx=='node':
        node_mode = 'node'
        break
    else:   
        print(f"Unsupported node mode: {node_mode}")


print(node_mode)