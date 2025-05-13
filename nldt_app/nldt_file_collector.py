# -*- coding: utf-8 -*-
"""
Created on Thu Apr 17 08:50:05 2025

@author: baeby
"""

import logging
logger = logging.getLogger("nldt_m")

import os
import hashlib
import json

class NLDT_File_Collector:
    def __init__(self, host):
        self.host = host
        self.source_dir = os.path.join("C:/","Support_FAS", "RESULT_TESTS" )
        self.outbox = []
        
    def list_files(self):
        files = os.listdir(self.source_dir)
        self.to_transfer = [ f for f in files if (f.endswith('.txt') or f.endswith('.json') or f.endswith('.xml'))]
        logger.info(f'Files to transfer : {len(self.to_transfer)}')
        
    def file_to_frames(self, filename):
        logger.info(f"file to frames: {filename}")
        filepath = os.path.join(self.source_dir, filename)
        with open(filepath, 'rb') as file:
            data = file.read()
            md5 = hashlib.md5(data).hexdigest()
            frame = { "host": self.host, "file": filename, "checksum": md5 }
            logger.info(frame)
            self.outbox.append(json.dumps(frame))
        
        with open(filepath, 'r') as file:
            
            lines = file.readlines()
            for line in lines:
                length = 128
                chunks = [line[i:i+length] for i in range(0, len(line), length)]
                for chunk in chunks:
                    frame = { "host": self.host, "chunk": chunk }
                    logger.info(frame)
                    self.outbox.append(json.dumps(frame))
            frame = { "host": self.host, "complete": 1 }
            self.outbox.append(json.dumps(frame))
    