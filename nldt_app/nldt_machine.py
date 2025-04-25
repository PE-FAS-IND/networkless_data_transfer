# -*- coding: utf-8 -*-
"""
Created on Thu Apr 17 15:35:30 2025

@author: baeby
"""



import logging

logger = logging.getLogger("nldt_m")
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
        time.sleep(2)
        self.trace_route()
        
    
    def trace_route(self):
        trace_msg = { "trace": ['1'],
                      "host": self.host }
        logger.info(f"Machine -> {trace_msg}")
        payload = json.dumps(trace_msg).encode('utf-8') + b"\r\n"
        logger.info(f"Machine -> {payload}")
        self.conn.write(payload)
        
    
    def process_local_dir(self):
        self.file_collector.list_files()
        logger.info(self.file_collector.to_transfer)
        for filename in self.file_collector.to_transfer:
            self.file_collector.file_to_frames(filename)
            for frame in self.file_collector.outbox:
                # print(frame)
                payload = frame.encode('utf-8') + b"\r\n"
                
                logger.info(payload)
                self.conn.write(payload)
                time.sleep(0.02)
            # Empty outbox
            self.file_collector.outbox = []
    
    def read_msg(self):
        if self.conn.in_waiting>0:
            msg = self.conn.readline()
            
            if msg.startswith(b'b'):
                msg_clean = msg.decode('utf-8')
                to_decode = f"{msg_clean.rstrip()}.decode('utf-8')"                    # print(to_decode)
                decoded = eval(to_decode)
                logger.info(decoded)
            else:
                # print(msg)
                ...
        
        

if __name__ == "__main__":
    m = NLDT_Machine('U1234567')