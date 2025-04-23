# -*- coding: utf-8 -*-
"""
Created on Thu Apr 17 15:35:30 2025

@author: baeby
"""



import logging

logger = logging.getLogger("nldt")

import gc
gc.enable()

import serial.tools.list_ports
import serial
import time

import nldt_file_collector


class NLDT_Machine:
    def __init__(self, host):
        self.host = host
        self.search_device()
        if len(self.devices)>0:
            d = self.devices[0]
            self.init_machine(d.device)
        self.file_collector = nldt_file_collector.NLDT_File_Collector(self.host)
        self.keep_alive = True
        
    def search_device(self):
        # List all available COM ports
        ports = serial.tools.list_ports.comports(include_links=True)
        self.devices = [port for port in ports if 'Silicon Labs CP210x' in port.description]
        
    def init_machine(self, port):
        self.conn = serial.Serial(port, 115200, timeout=1)
        self.conn.write(b'node\r\n')
    
    def process_local_dir(self):
        self.file_collector.list_files()
        logger.info(self.file_collector.to_transfer)
        self.file_collector.file_to_frames(self.file_collector.to_transfer[0])
        for frame in self.file_collector.outbox:
            # print(frame)
            payload = frame.encode('utf-8') + b"\r\n"
            
            logger.info(payload)
            self.conn.write(payload)
            time.sleep(0.05)
        # Empty outbox
        self.file_collector.outbox = []
        

if __name__ == "__main__":
    m = NLDT_Machine('U1234567')