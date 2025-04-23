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

logger = logging.getLogger("nldt")

class NLDT_Inbox:
    """
    """
    
    def __init__(self, host):
        self.host = host
        self.route = None
        self.inbox_path = os.path.join(".", "inbox", host)
        if not os.path.isdir(self.inbox_path):
            os.makedirs(self.inbox_path, exist_ok=True)
    
    def set_route(self, route):
        self.route = route
        
    def process_message(self, obj):
        # print(obj)
        if "file" in obj:
            # print('file in obj')
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
            else:
                logger.info(f"Received: {self.file} - checksum not valid")
                os.remove(self.path)
            
            # Reset all file related values
            self.path = None
            self.file = None
            self.checksum = None
        else:
            print('Unknown frame')
                