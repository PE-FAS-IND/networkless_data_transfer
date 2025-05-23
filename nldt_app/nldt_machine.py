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
import threading
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
        self.uart_outbox = []
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
        self.keep_alive = True
        try:
            self.conn = serial.Serial(self.port, 115200, timeout=10) 
            self.reboot_esp32()
            self.uart_outbox.insert(0, json.dumps({"role":"node"}))
            time.sleep(0.2)
            self.uart_outbox.insert(0, json.dumps({"cleanup":"empty"}))
            self.start_threads()
            time.sleep(2)
            self.trace_route()
        except Exception as e:
            try:
                self.conn.close()
            except:
                pass
            self.stop_threads()
        
        
    def reboot_esp32(self):
        self.conn.setRTS(1)
        time.sleep(0.1)
        self.conn.setRTS(0)
        time.sleep(4)
    
    def trace_route(self):
        trace_msg = { "trace": [],
                      "host": self.host }
        self.uart_outbox.insert(0, json.dumps(trace_msg))
    
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
                self.uart_outbox.insert(0, frame)
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
        try:
            if self.conn.in_waiting>0:
                msg = self.conn.readline()
                logger.info(f"<-- {msg}")
                
                msg_clean = msg.decode('utf-8').rstrip()
                self.uart_inbox.insert(0, msg_clean)
            else:
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"COM error - restart app -- {e}")
            self.stop_threads()
            
                            
        
    
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
    
    def process_uart_outbox(self):
        if len(self.uart_outbox)>0:
            msg = self.uart_outbox.pop()
            logger.info(f"uart -> {msg}")
            payload =  msg.rstrip().encode('utf-8') + b"\r\n"
            try:
                self.conn.write(payload)
            except Exception as e:
                logger.error(f"Error uart_outbox -- {e}")
        else:
            time.sleep(0.1)
    
    def task_uart_outbox(self):
        while self.keep_alive:
            self.process_uart_outbox()
        
    def start_threads(self):
        logger.info("Start threads")
        self.stopFlag = threading.Event()
        
        self.keep_alive = True
        self.thread_uart = threading.Thread(target=self.task_uart)
        self.thread_uart.start()
        
        self.thread_uart_inbox = threading.Thread(target=self.task_uart_inbox)
        self.thread_uart_inbox.start()
        
        self.thread_uart_outbox = threading.Thread(target=self.task_uart_outbox)
        self.thread_uart_outbox.start()
        
        self.thread_process_local_dir = threading.Thread(target=self.task_process_local_dir)
        self.thread_process_local_dir.start()
        
        self.thread_trace_route = threading.Thread(target=self.task_trace_route)
        self.thread_trace_route.start()
                
    
    def stop_threads(self):
        logger.info("Stop threads")
        self.keep_alive = False
        try:
            self.thread_uart.join()
        except Exception as e:
            logger.info(f"thread_uart -- {e}")
        
        try:
            self.thread_uart_inbox.join()
        except Exception as e:
            logger.info(f"thread_uart_inbox -- {e}")
            logger.info(e)
        
        try:
            self.thread_uart_outbox.join()
        except Exception as e:
            logger.info(f"thread_uart_outbox -- {e}")
            logger.info(e)
            
        try:
            self.thread_process_local_dir.join()
        except Exception as e:
            logger.info(f"thread_process_local_dir -- {e}")
            logger.info(e)
        
        logger.info("Threads stopped")
        time.sleep(10)
        self.init_machine()
        
        

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
        logger.info('------------------END-------------------')
        logger.info(e)
        
        