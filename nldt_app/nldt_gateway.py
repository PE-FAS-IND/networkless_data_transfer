# -*- coding: utf-8 -*-
"""
Created on Wed Apr 16 13:47:43 2025

@author: baeby

State machine:
    1 - look for a device
    2 - connect serial
    3 - start device as gateway
    4 - process incomming serial frames
    5 - if an error occurs --> close conn and goto state 1
"""


import logging

logger = logging.getLogger("nldt")

import gc
gc.enable()

import serial.tools.list_ports
import serial
import time

import nldt_dispatcher


class NLDT_Gateway:
    def __init__(self):
        self.search_device()
        if len(self.devices)>0:
            d = self.devices[0]
            self.init_gateway(d.device)
        self.dispatcher = nldt_dispatcher.NLDT_Dispatcher()
        self.keep_alive = True
        self.listen()        
        
    def search_device(self):
        # List all available COM ports
        ports = serial.tools.list_ports.comports(include_links=True)
        self.devices = [port for port in ports if 'Silicon Labs CP210x' in port.description]
        
    def init_gateway(self, port):
        self.conn = serial.Serial(port, 115200, timeout=10)
        self.conn.write(b'gateway\r\n')
    
    def listen(self):
        while self.keep_alive:
            if self.conn.in_waiting:
                msg = self.conn.readline()
                
                if msg.startswith(b'b'):
                    print(msg.decode('utf-8')[2:-4])
                else:
                    print(msg)
                # self.dispatcher.process_message(msg)
        

