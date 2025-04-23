# -*- coding: utf-8 -*-
"""
Created on Wed Apr 16 11:27:03 2025

@author: baeby
"""
import logging
logger = logging.getLogger("nldt")

import nldt_inbox
import json

class NLDT_Dispatcher:
    def __init__(self):
        self.inboxes = []
        
    def get_inbox(self, host):
        inbox_list = [inbox for inbox in self.inboxes if inbox.host==host]
        if len(inbox_list)==0:
            inbox = nldt_inbox.NLDT_Inbox(host)
            self.inboxes.append(inbox)
        else:
            inbox = inbox_list[0]        
        return inbox
    
    def process_message(self, msg):
        # print(f"Dispatcher: incomming msg = {msg}")
        try:
            obj = json.loads(msg)
            host = obj['host']
            inbox = self.get_inbox(host)
            inbox.process_message(obj)
        except Exception as e:
            # logger.info(f"Msg not processed ({e})")
            ...
        