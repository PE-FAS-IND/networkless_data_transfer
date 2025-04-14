# -*- coding: utf-8 -*-
"""
Created on Wed Apr  2 08:55:11 2025

@author: baeby
"""

import gc
gc.enable()

import serial.tools.list_ports
import serial
import os
import time
import shutil


port_node = "COM4"
RESULT_DIR = r"C:\Support_FAS\RESULT_TESTS"

# List all available COM ports
# ports = serial.tools.list_ports.comports(include_links=True)

# Print each port
# for port in ports:
#     if 'Silicon Labs CP210x' in port.description:
#         print(f"Found device on port: {port.device}")
        
# timeout = 10



conn_node = serial.Serial(port_node, 115200, timeout=10)
tx_node = conn_node.write(b'node\n')
rx_node = conn_node.readline()




def ser_write(msg):
    payload = msg.rstrip().encode('utf-8') + b'\n'
    print(f"--> {payload}")
    conn_node.write(payload)
    time.sleep(0.05)

def transfer_files():
    toTransfer = [f for f in os.listdir(RESULT_DIR) if os.path.isfile(os.path.join(r"C:\Support_FAS\RESULT_TESTS", f))]
    print(toTransfer)
    for f in toTransfer:
        filepath = os.path.join(r"C:\Support_FAS\RESULT_TESTS", f)
        print(filepath)
        
        with open(filepath) as f_:
            ser_write('file_transfer_begin\n')
            ser_write(f'{f}\n')
            for l in f_.readlines():
                ser_write(f'{l}\n')
            ser_write('file_transfer_end\n')
        shutil.copy2(os.path.join(r"C:\Support_FAS\RESULT_TESTS", f), os.path.join(r"C:\Support_FAS\RESULT_TESTS\moved", f))
        os.remove(os.path.join(r"C:\Support_FAS\RESULT_TESTS", f))

while True:
    time.sleep(10)
    transfer_files()
    
conn_node.close()
