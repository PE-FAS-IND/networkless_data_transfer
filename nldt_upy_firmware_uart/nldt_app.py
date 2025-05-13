import machine
from machine import UART
from machine import Pin
from neopixel import NeoPixel
import uselect
import espnow
import network
import binascii
import ujson
import _thread
import time

pin = Pin(8, Pin.OUT)   # set GPIO0 to output to drive NeoPixels
np = NeoPixel(pin, 8)   # create NeoPixel driver on GPIO0 for 8 pixels

def set_led_color(color=(20, 20, 20)):
    np[0] = color # set the first pixel to white
    np.write()

set_led_color(color=(20, 0, 0))
time.sleep_ms(500)
set_led_color(color=(0, 20, 0))
time.sleep_ms(500)
set_led_color(color=(0, 0, 20))
time.sleep_ms(500)
set_led_color(color=(20, 0, 0))

class NLDT_APP:
    def __init__(self):
        print('init NLDT_APP')
        self.long_uid = binascii.hexlify(machine.unique_id()).decode('utf-8')
        print(self.long_uid)
        # Role = node or gateway
        self.role = None
        self.level = 1000
        self.favourite_node = None
        self.e = None
        self.b_peer = b'\xbb\xbb\xbb\xbb\xbb\xbb'
        # Init variables
        self.buffer = b''
        self.uart_inbox = []
        self.uart_outbox = []
        self.espnow_inbox = []
        self.espnow_outbox = []
        # Init COMs
        self.init_uart()
        self.init_espnow()

        # Start threads
        self.start_threads()

    # UART
    def init_uart(self):
        self.uart = UART(1, 115200) 
        self.uart.init(115200, bits=8, parity=None, stop=1, tx=9, rx=10)
        print('uart ready')

    def read_lines(self):
        if self.uart.any():
            data = self.uart.read()  # read all available bytes
            if data:
                self.buffer += data
                while b'\n' in self.buffer:
                    line, self.buffer = self.buffer.split(b'\n', 1)
                    line_str = line.decode('utf-8').rstrip('\r')
                    print(f"uart <- {line_str}")
                    self.uart_inbox.insert(0, line_str)
        else:
            time.sleep_ms(100)
    
    def uart_polling(self):
        while True:
            self.read_lines()
    
    # ESPNOW
    def init_espnow(self):
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        self.e = espnow.ESPNow()
        self.e.active(True)

    def espnow_listening(self):
        while True:
            host, msg = self.e.recv()
            if msg:
                self.espnow_inbox.insert(0, (host, msg))
    
    # Processing UART inbox
    def process_uart_inbox(self):
        while True:
            if len(self.uart_inbox)>0:
                msg = self.uart_inbox.pop()
                # print(f"processing uart_inbox : {msg} -end-")
                msg_json = ujson.loads(msg)
                
                if self.role == 'gateway':
                    if 'trace' in msg_json:
                        self.uart_outbox.insert(0, ujson.dumps(msg_json))
                    elif 'dest' in msg_json:
                        dest = msg_json['dest']
                        route = msg_json['route']
                        next = route.pop()
                        msg_json['route'] = route
                        self.espnow_outbox.insert(0,(next, ujson.dumps(msg_json)))
                    else:
                        print(f'Unattended frame : {msg_json}')

                elif self.role == 'node':
                    if 'trace' in msg_json:
                        msg_json['trace'] = [self.long_uid]
                        print(f"e_outbox + {self.favourite_node} :: {msg_json}")
                        self.espnow_outbox.insert(0,(self.favourite_node, ujson.dumps(msg_json)))
                    elif 'file' in msg_json:
                        print(f"e_outbox + {self.favourite_node} :: {msg_json}")
                        self.espnow_outbox.insert(0,(self.favourite_node, ujson.dumps(msg_json)))
                    elif 'chunk' in msg_json:
                        print(f"e_outbox + {self.favourite_node} :: {msg_json}")
                        self.espnow_outbox.insert(0,(self.favourite_node, ujson.dumps(msg_json)))
                    elif 'complete' in msg_json:
                        print(f"e_outbox + {self.favourite_node} :: {msg_json}")
                        self.espnow_outbox.insert(0,(self.favourite_node, ujson.dumps(msg_json)))
                    elif 'dest' in msg_json:
                        dest = msg_json['dest']
                        route = msg_json['route']
                        next = route.pop()
                        if dest==next:
                            self.uart_outbox.insert(0, ujson.dumps(msg_json))
                        else:
                            msg_json['route'] = route
                            self.espnow_outbox.insert(0,(next, ujson.dumps(msg_json)))
                    else:
                        print(f'Unattended frame : {msg_json}')

                else:
                    if 'role' in msg_json:
                        self.role = msg_json['role']
                        if self.role == 'gateway':
                            self.level = 0
                            self.uart_outbox.insert(0,'ok bob, gw')
                            set_led_color((25, 7, 0))

                        elif self.role == 'node':
                            self.uart_outbox.insert(0,'ok bob, node')
                            set_led_color((0,0,20))
                    else:
                        print(f"{msg_json} received before getting a role")
            else:
                time.sleep_ms(100)

    # Processing UART outbox
    def process_uart_outbox(self):
        while True:
            if len(self.uart_outbox)>0:
                msg = self.uart_outbox.pop()
                print(f"uart -> {msg}")
                payload = msg.encode('utf-8') + b"\r\n"
                self.uart.write(payload)
            else:
                time.sleep_ms(100)


    # Processing ESPNOW inbox
    def process_espnow_inbox(self):
        while True:
            if len(self.espnow_inbox)>0:
                (host, msg) = self.espnow_inbox.pop()
                print(f"e <- {host} :: {msg}")
                msg_json = ujson.loads(msg)
                if 'ping' in msg_json:
                    ping_level = msg_json['level']
                    if (ping_level + 1)<self.level:
                        self.level = ping_level + 1
                        self.favourite_node = msg_json['ping']
                        self.level_time = time.ticks_ms()
                    elif (ping_level + 1)==self.level:
                        self.favourite_node = msg_json['ping']
                        self.level_time = time.ticks_ms()
                    else:
                        ...
                        
                    pong = {"pong": self.long_uid, "level": self.level}
                    self.espnow_outbox.insert(0,(host, ujson.dumps(pong)))
                    
                elif 'pong' in msg_json:
                    ...
                else:
                    if self.role == 'gateway':
                        self.uart_outbox.insert(0, ujson.dumps(msg_json))

                    elif self.role == 'node':
                        if 'trace' in msg_json:
                            trace =  msg_json['trace']
                            msg_json['trace'] = trace.append(self.long_uid)
                            self.espnow_outbox.insert(self.favourite_node, ujson.dumps(msg_json))
                        elif 'dest' in msg_json:
                            dest = msg_json['dest']
                            # If node is dest, output to uart
                            if dest==self.long_uid:
                                self.uart_outbox.insert(0, ujson.dumps(msg_json))
                            else:
                                route = msg_json['route']
                                next = route.pop()
                                msg_json['route'] = route
                                self.espnow_outbox.insert(next, ujson.dumps(msg_json))
                        else:
                            self.espnow_outbox.insert(self.favourite_node, ujson.dumps(msg_json))
                    else:
                        ...
            else:
                time.sleep_ms(100)

    # Processing ESPNOW outbox   
    def process_espnow_outbox(self):
        while True:
            if len(self.espnow_outbox)>0 and self.e:
                (host, msg) = self.espnow_outbox.pop()
                try:
                    # Check host is in bytes
                    if type(host)==str:
                        host = binascii.unhexlify(host)

                    msg_json = ujson.loads(msg)

                    print(f"e -> {host} ({len(host)}, {type(host)}) :: {msg_json}")

                    self.e.add_peer(host)
                    self.e.send(host, ujson.dumps(msg_json))
                    self.e.del_peer(host)
                except Exception as err:
                    print(err)
                    print(f"fav = {self.favourite_node}")
                    print(f"host = {host}")
                    print(type(host))
            else:
                time.sleep_ms(100)
                

    # Ping:
    def espnow_ping(self):
        while True:
            time.sleep(4)
            ping = { "ping": self.long_uid, "level": self.level }
            self.espnow_outbox.append((self.b_peer, ujson.dumps(ping))) 

    # Start threads
    def start_threads(self):
        # Start UART polling
        _thread.start_new_thread(self.uart_polling, ())

        # Start ESPNOW polling
        _thread.start_new_thread(self.espnow_listening, ())

        # Start in/out boxes processing
        _thread.start_new_thread(self.process_uart_inbox, ())
        _thread.start_new_thread(self.process_uart_outbox, ())
        
        _thread.start_new_thread(self.process_espnow_inbox, ())
        _thread.start_new_thread(self.process_espnow_outbox, ())
        
        _thread.start_new_thread(self.espnow_ping, ())


