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

logger = logging.getLogger("nldt_gw")
logging.basicConfig(level=logging.INFO,
    format="{asctime} | {filename:12.12s} {lineno:d} | {levelname:8} | {message}",
    style='{'
    )

import gc
gc.enable()

import serial.tools.list_ports
import serial
import time
import json

import nldt_dispatcher


class NLDT_Gateway:
    def __init__(self, port=None):
        self.port = port
        self.search_device()

        if len(self.devices)>0:
            if not port:
                self.port = self.devices[0].name
            
            self.init_gateway(self.port)
        else:
            return "No device available"
            
                
        self.dispatcher = nldt_dispatcher.NLDT_Dispatcher()
        self.keep_alive = True
        self.listen()        
        
    def search_device(self):
        # List all available COM ports
        ports = serial.tools.list_ports.comports(include_links=True)
        self.devices = [port for port in ports if "USB Serial Port" in port.description]
        
    def init_gateway(self, port):
        self.conn = serial.Serial(port, 115200, timeout=10)
        self.conn.write(b'{"role":"gateway"}\r\n')
    
    def listen(self):
        while self.keep_alive:
            if self.conn.in_waiting:
                msg = self.conn.readline()
                logger.info(f"<-- {msg} {msg.startswith(b'b')}")
                try:
                    msg_clean = msg.decode('utf-8').rstrip()
                    confirmation = self.dispatcher.process_message(msg_clean)
                    if confirmation:
                        logger.info('Confirm to gateway')
                        logger.info(confirmation)
                        # TODO:debug!!
                        payload = json.dumps(confirmation).encode('utf-8') + b"\r\n"
                        logger.info(payload)
                        self.conn.write(payload)
                except Exception as e:
                    print(e)
                    ...
                
        

if __name__ == "__main__":
    gw = NLDT_Gateway(port='COM11')
