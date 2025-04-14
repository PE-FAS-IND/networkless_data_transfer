# -*- coding: utf-8 -*-
"""
Created on Tue Apr  1 16:40:32 2025

@author: baeby
"""


import gc
gc.enable()

import serial.tools.list_ports
import serial
import time

port_gw = "COM8"

# List all available COM ports
# ports = serial.tools.list_ports.comports(include_links=True)

# # Print each port
# for port in ports:
#     if 'Silicon Labs CP210x' in port.description:
#         print(f"Found device on port: {port.device}")
        
timeout = 10

conn_gw = serial.Serial(port_gw, 115200, timeout=10)
tx_gw = conn_gw.write(b'gateway\n')
rx_gw = conn_gw.readline()
print(rx_gw)


def get_msg():
    msg = str(conn_gw.readline())
    msg = msg.replace("b'\"", '').replace('\\\\n"\\r\\n\'', '')
    mac = msg[0:12]
    data = msg[12:]
    return mac, data


content = b''

while True:
    toRead = conn_gw.inWaiting()
    if toRead>0:
        mac, data = get_msg()
        print(f"received from {mac}: {data}")
        print('--------------------------------')
        if data.startswith('file_transfer_begin'):
            print('yoohoo')
            mac, filename = get_msg()
            content = ""
            payload = ""
            continueReading = True
            while continueReading:
                mac, data = get_msg()
                if data.startswith("file_transfer_end"):
                    continueReading = False
                else:
                    content = content + data + '\n'
            # content = bytes(content.decode('utf-8')[2:-3], 'utf-8').decode('utf-8')
            # content = content.replace('\\r\\n', '\n')
            print(f"Receive : {filename}")
            
            
            
            with open(f"./inbox/{filename}", "a") as f:
                print(content)
                f.write(content)
                f.close()
            
            continueReading = True
            msg = ''
            
    else:
        time.sleep(0.01)


conn_gw.close()
