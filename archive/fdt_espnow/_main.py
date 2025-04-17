# main.py -- put your code here!
import sys
import time
from machine import Pin
from neopixel import NeoPixel
import _thread

pin = Pin(8, Pin.OUT)   # set GPIO0 to output to drive NeoPixels
np = NeoPixel(pin, 8)   # create NeoPixel driver on GPIO0 for 8 pixels
np[0] = (255, 255, 255) # set the first pixel to white
np.write()              # write data to all pixels
# r, g, b = np[0]     

def serial_com():
    while True:
        np[0] = (0,0,20)
        np.write()
        time.sleep_ms(500)
        try:
            rx = sys.stdin.readline()
            np[0] = (0,20,0)
            np.write()
            time.sleep_ms(200)
            if rx == "b'gateway\n'":
                np[0] = (0,30,30)
                np.write()
                time.sleep_ms(1500)
            elif rx == "b'node\n'":
                np[0] = (30,30,0)
                np.write()
                time.sleep_ms(1500)
            else:
                np[0] = (10,80,20)
                np.write()
                time.sleep_ms(1500)
        except:
            np[0] = (128,0,0)
            np.write()
            time.sleep_ms(500)

_thread.start_new_thread(serial_com, ())