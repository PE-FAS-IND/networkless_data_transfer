from machine import UART
import uselect

uart = UART(1, 115200) 
uart.init(115200, bits=8, parity=None, stop=1, tx=9, rx=10)

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


def uart_polling(inbox, outbox):
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
            