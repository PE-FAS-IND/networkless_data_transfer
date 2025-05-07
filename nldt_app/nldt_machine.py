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
from threading import Thread
import shutil
import os

import nldt_file_collector


class NLDT_Machine:
    def __init__(self, host, port=None, period=15):
        self.host = host
        self.port = port
        self.period = period
        self.uart_inbox = []        
        self.search_device()       
        
        if len(self.devices)>0:
            if not port:
                self.port = self.devices[0].name
            
            self.init_machine(self.port)
        else:
            logger.info("No device available")
            return "No device available"
        
        self.file_collector = nldt_file_collector.NLDT_File_Collector(self.host)
        self.keep_alive = True
        self.start_threads()
        
    def search_device(self):
        # List all available COM ports
        ports = serial.tools.list_ports.comports(include_links=True)
        self.devices = [port for port in ports if 'USB Serial Port' in port.description]
        
    def init_machine(self, port):
        self.conn = serial.Serial(port, 115200, timeout=1)
        self.conn.write(b'{"role":"node"}\r\n')
        time.sleep(2)
        self.trace_route()
        
    
    def trace_route(self):
        trace_msg = { "trace": [],
                      "host": self.host }
        logger.info(f"Machine -> {trace_msg}")
        payload = json.dumps(trace_msg).encode('utf-8') + b"\r\n"
        logger.info(f"Machine -> {payload}")
        self.conn.write(payload)
        
    
    def process_local_dir(self):
        self.file_collector.list_files()
        # logger.info(self.file_collector.to_transfer)
        for filename in self.file_collector.to_transfer:
            self.file_collector.file_to_frames(filename)
            for frame in self.file_collector.outbox:
                # print(frame)
                payload = frame.encode('utf-8') + b"\r\n"
                
                # logger.info(payload)
                self.conn.write(payload)
                time.sleep(0.1)
            # Empty outbox
            self.file_collector.outbox = []
    
    def task_process_local_dir(self):
        while self.keep_alive:
            self.process_local_dir()
            time.sleep(self.period)
    
    def read_msg(self):
        if self.conn.in_waiting>0:
            msg = self.conn.readline()
            logger.info(f"<-- {msg}")
            try:
                msg_clean = msg.decode('utf-8').rstrip()
                self.uart_inbox.insert(0, msg_clean)
            except Exception as e:
                print(e)
    
    def task_uart(self):
        while self.keep_alive:
            self.read_msg()
            
    
    def process_uart_inbox(self):
        if len(self.uart_inbox)>0:
            msg = self.uart_inbox.pop()
            logger.info(f"uart <- {msg}")
            try:
                msg_json = json.loads(msg)
                if 'confirm' in msg_json:
                    filename = msg_json['confirm']
                    src_dir = self.file_collector.source_dir
                    dest_dir = os.path.join(src_dir, "moved")
                    if not os.path.isdir(dest_dir):
                        os.makedirs(dest_dir, exist_ok=True)
                    src = os.path.join(src_dir, filename)
                    dest = os.path.join(self.file_collector.source_dir, "moved", filename)
                    try:
                        shutil.copy2(src, dest)
                        os.remove(src)
                    except:
                        ...
            except Exception as e:
                logger.info(e)
    
    def task_uart_inbox(self):
        while self.keep_alive:
            self.process_uart_inbox()
    
    def start_threads(self):
        logger.info("Start threads")
        
        self.task_uart = Thread(target=self.task_uart)
        self.task_uart.start()
        
        self.task_uart_inbox = Thread(target=self.task_uart_inbox)
        self.task_uart_inbox.start()
        
        self.task_process_local_dir = Thread(target=self.task_process_local_dir)
        self.task_process_local_dir.start()
                
    
    def stop_threads(self):
        logger.info("Stop threads")
        self.keep_alive = False
        self.task_uart.join()
        self.task_uart_inbox.join()
        self.task_process_local_dir.join()
        logger.info("Threads stopped")
        
        

if __name__ == "__main__":
    m = NLDT_Machine('U1234567', port='COM12')