# -*- coding: utf-8 -*-
"""
Created on Thu Apr 17 15:35:30 2025

@author: baeby
"""



import logging

from datetime import datetime
today = datetime.today().strftime("%Y-%m-%d")
log_filename = f"./log/nldt_{today}.log"
logger = logging.getLogger("nldt_m")
logger.setLevel(logging.INFO)

logFormatter = logging.Formatter("{asctime} | {filename:12.12s} {lineno:d} | {levelname:8} | {message}", style='{')

fileHandler = logging.FileHandler(log_filename)
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

logger.info('startup')

import gc
gc.enable()

import serial.tools.list_ports
import serial
import time
import json
from threading import Thread
import shutil
import os
import socket
import sys

import nldt_file_collector


class NLDT_Machine:
    def __init__(self, host=None, port=None, period=15):
        if host:
            self.host = host
        else:
            self.host = socket.gethostname()
        
        self.period = period
        self.uart_inbox = []
        self.busy = False
        self.search_device()
        if port:
            self.port = port
        else:
            self.port = self.devices[0].name      
        
        
        self.file_collector = nldt_file_collector.NLDT_File_Collector(self.host)
        self.keep_alive = True
        self.init_machine()
        
        
    def search_device(self):
        # List all available COM ports
        ports = serial.tools.list_ports.comports(include_links=True)
        self.devices = [port for port in ports if 'USB Serial Port' in port.description]
        
    def init_machine(self):
        self.conn = serial.Serial(self.port, 115200, timeout=10)   
        self.reboot_esp32()
        self.conn.write(b'{"role":"node"}\r\n')
        time.sleep(0.2)
        self.conn.write(b'{"cleanup":"empty"}\r\n')
        self.start_threads()
        time.sleep(2)
        self.trace_route()
        
    def reboot_esp32(self):
        self.conn.setRTS(1)
        time.sleep(0.1)
        self.conn.setRTS(0)
        time.sleep(4)
    
    def trace_route(self):
        trace_msg = { "trace": [],
                      "host": self.host }
        logger.info(f"Machine -> {trace_msg}")
        payload = json.dumps(trace_msg).encode('utf-8') + b"\r\n"
        logger.info(f"Machine -> {payload}")
        self.conn.write(payload)
    
    def task_trace_route(self):
        while self.keep_alive:
            time.sleep(2 * self.period)
            self.trace_route()
    
    def process_local_dir(self):
        self.file_collector.list_files()
        # logger.info(self.file_collector.to_transfer)
        self.busy = True
        for filename in self.file_collector.to_transfer:
            self.file_collector.file_to_frames(filename)
            for frame in self.file_collector.outbox:
                # print(frame)
                payload = frame.encode('utf-8') + b"\r\n"
                
                # logger.info(payload)
                self.conn.write(payload)
                time.sleep(0.3)
            # Empty outbox
            self.file_collector.outbox = []
        self.busy = False
    
    def task_process_local_dir(self):
        while self.keep_alive:
            time.sleep(self.period)
            if not self.busy:
                self.process_local_dir()            
    
    def read_msg(self):
        if self.conn.in_waiting>0:
            msg = self.conn.readline()
            logger.info(f"<-- {msg}")
            try:
                msg_clean = msg.decode('utf-8').rstrip()
                self.uart_inbox.insert(0, msg_clean)
            except Exception as e:
                print(e)
                                
        else:
            time.sleep(0.1)
    
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
        else:
            time.sleep(0.1)
    
    def task_uart_inbox(self):
        while self.keep_alive:
            self.process_uart_inbox()
    
    def start_threads(self):
        logger.info("Start threads")
        
        self.thread_uart = Thread(target=self.task_uart)
        self.thread_uart.start()
        
        self.thread_uart_inbox = Thread(target=self.task_uart_inbox)
        self.thread_uart_inbox.start()
        
        self.thread_process_local_dir = Thread(target=self.task_process_local_dir)
        self.thread_process_local_dir.start()
        
        self.thread_trace_route = Thread(target=self.task_trace_route)
        self.thread_trace_route.start()
                
    
    def stop_threads(self):
        logger.info("Stop threads")
        self.keep_alive = False
        self.thread_uart.join()
        self.thread_uart_inbox.join()
        self.thread_process_local_dir.join()
        logger.info("Threads stopped")
        
        

if __name__ == "__main__":
    try:
        with open("./settings.json") as f:
            settings = json.loads(f.read())
            if 'machine' in settings:
                machine = settings['machine']
            if 'port' in settings:
                port = settings['port']
            logger.info(machine)
            logger.info(port)
            
    except Exception as e:
        logger.info(e)
        machine = None
        port = None
        
    logger.info(f"startup, machine={machine}, port={port}")
    try:
        m = NLDT_Machine(host=machine, port=port)
    except Exception as e:
        logger.info(e)
        
        