# -*- coding: utf-8 -*-
"""
Created on Tue Apr 15 11:30:01 2025

@author: baeby
"""

import json
import os
import re
import hashlib
import logging

logger = logging.getLogger("nldt_gw")
logging.basicConfig(level=logging.INFO,
    format="{asctime} | {filename:12.12s} {%(lineno)d} | {levelname:8} | {message}",
    style='{'
    )


class NLDT_Inbox:
    """
    """
    
    def __init__(self, host):
        self.host = host
        self.route = []
        self.inbox_path = os.path.join(".", "inbox", host)
        if not os.path.isdir(self.inbox_path):
            os.makedirs(self.inbox_path, exist_ok=True)
    
        
    def process_message(self, obj):
        # logger.info(obj)
        if "trace" in obj:
            # logger.info('trace in obj')
            logger.info(f"Route = {obj['trace']}")
            self.route = obj['trace']
            logger.info(f"{self.host} et route = {self.trace}")
                    
        elif "file" in obj:
            logger.info('file in obj')
            self.file = obj['file']
            self.checksum = obj['checksum']
            self.path = os.path.join(self.inbox_path, self.file)
            with open(self.path, 'w') as f:
                f.close()
            
        elif "chunk" in obj:
            # print('chunk')
            with open(self.path, 'a') as f:
                f.write(obj['chunk'])
                f.close()
                
        elif "complete" in obj:
            # print('complete')
            with open(self.path, 'rb') as f:
                data = f.read()
                md5_returned = hashlib.md5(data).hexdigest()
                # print(f'md5 = {md5_returned}')
            if md5_returned == self.checksum:
                logger.info(f"Received: {self.file} - checksum valid")
                logger.info(self.file)
                logger.info(self.route)
                logger.info(self.host)
                
                confirmation = { 
                    "dest": self.route[0],
                    "route": self.route,
                    "confirm": self.file 
                    } 
            else:
                logger.info(f"Received: {self.file} - checksum not valid")
                os.remove(self.path)
                confirmation = None
                
            # Reset all file related values
            self.path = None
            self.file = None
            self.checksum = None
            
            logger.info(confirmation)
            
            return confirmation
        
        else:
            print('Unknown frame')
            
                