import sys
from machine import Pin
from neopixel import NeoPixel
from machine import UART
import uselect

uart = UART(1, 115200) 
uart.init(115200, bits=8, parity=None, stop=1, tx=9, rx=10)

pin = Pin(8, Pin.OUT)   # set GPIO0 to output to drive NeoPixels
np = NeoPixel(pin, 8)   # create NeoPixel driver on GPIO0 for 8 pixels
np[0] = (20, 0, 0) # set the first pixel to white
np.write()


global node_mode
node_mode = None

# while not node_mode:
#     rx = uart.readline()
#     if rx=='gateway':
#         node_mode = 'gateway'
#         break
#     elif rx=='node':
#         node_mode = 'node'
#         break
#     else:   
#         print(f"Unsupported node mode: {node_mode}")

# print(node_mode)

buffer = b''

def read_lines():
    global buffer
    lines = []
    if uart.any():
        data = uart.read()  # read all available bytes
        if data:
            buffer += data
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                lines.append(line.decode('utf-8').rstrip('\r'))
    return lines

# Usage in main loop
while True:
    lines = read_lines()
    for line in lines:
        print("Received line:", line, "-end-")
        if line.startswith('gateway'):
            node_mode = 'gateway'
            break
        elif line.startswith('node'):
            node_mode = 'node'
            break
        else:   
            print(f"Unsupported node mode: {node_mode}")
        
    if node_mode:
            break
        
print(node_mode)