# -*- coding: utf-8 -*-
"""
Created on Wed Apr 16 08:40:40 2025

@author: baeby
"""

import logging

logger = logging.getLogger("nldt")


print('Test startup')

# msgs = ['{ "mac":"aabbcc000000", "file": "test_0.txt", "checksum": "38e4fe170cc932b5c6e07478b44ba9f2" }',
#         '{ "mac":"aabbcc000000", "chunk": "DATE_ENR:20250407_150000#\\n" }',
#         '{ "mac":"aabbcc000000", "chunk": "CODE_PRODUIT:12-216C-00341_D3WFIL_42mA_288Ohm#\\n" }',
#         '{ "mac":"aabbcc000000", "complete": 1 }',
#         '{ "mac":"aabbcc111111", "file": "test_1.txt", "checksum": "fa2bcf7500a4fad2770c1121f2824e30" }',
#         '{ "mac":"aabbcc111111", "chunk": "DATE_ENR:20250407_151111#\\n" }',
#         '{ "mac":"aabbcc111111", "chunk": "CODE_PRODUIT:12-216C-00341_D3WFIL_42mA_288Ohm#\\n" }',
#         '{ "mac":"aabbcc111111", "complete": 1 }'
#         ]


# msgs_mix = ['{ "mac":"aabbcc000000", "file": "test_3.txt", "checksum": "8f11c3eb7adea6641ed8c8b983026269" }',
#         '{ "mac":"aabbcc111111", "file": "test_4.txt", "checksum": "7983c6b1afb68916472b6497943a2d90" }',
#         '{ "mac":"aabbcc111111", "chunk": "DATE_ENR:20250407_154444#\\n" }',
#         '{ "mac":"aabbcc000000", "chunk": "DATE_ENR:20250407_153333#\\n" }',
#         '{ "mac":"aabbcc000000", "chunk": "CODE_PRODUIT:12-216C-00341_D3WFIL_42mA_288Ohm#\\n" }',
#         '{ "mac":"aabbcc000000", "complete": 1 }',
#         '{ "mac":"aabbcc111111", "chunk": "CODE_PRODUIT:12-216C-00341_D3WFIL_42mA_288Ohm#\\n" }',
#         '{ "mac":"aabbcc111111", "complete": 1 }'
#         ]


import nldt_file_collector
fc = nldt_file_collector.NLDT_File_Collector('U1234567')
fc.list_files()
fc.file_to_frames(fc.to_transfer[0])
fc.list_files()

import nldt_dispatcher
dispatcher = nldt_dispatcher.NLDT_Dispatcher()

for frame in fc.outbox:
    dispatcher.process_message(frame)
