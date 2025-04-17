from machine import Pin
import machine
from neopixel import NeoPixel
import _thread
import espnow
import network
import binascii
import ujson
import uselect
import time
import sys

def write_serial(data):
    data = data
    sys.stdout.write(f"{data}\r\n")


pin = Pin(8, Pin.OUT)   # set GPIO0 to output to drive NeoPixels
np = NeoPixel(pin, 8)   # create NeoPixel driver on GPIO0 for 8 pixels

def set_led_color(color=(20, 20, 20)):
    np[0] = color # set the first pixel to white
    np.write()

set_led_color(color=(0, 0, 20))

sta = network.WLAN(network.STA_IF)
sta.active(True)

long_uid = binascii.hexlify(machine.unique_id()).decode('utf-8')
write_serial(long_uid)

e = espnow.ESPNow()
e.active(True)
node_level = 1000

peer = b'\xbb\xbb\xbb\xbb\xbb\xbb'          # Multiple broadcast
e.add_peer(peer)

favourite_node = None

def esp_loop():
    global node_level
    global favourite_node
    global long_uid

    while True:
        host, msg = e.recv()
        if msg:             # msg == None if timeout in recv()
            # print(host, msg)
            set_led_color((20,0,0))
            time.sleep_ms(20)
            set_led_color((0,0,20))
            try:
                msg_json = ujson.loads(msg)
                if 'level' in msg_json:
                    level = msg_json['level']
                    # print(f"{host} is level {level} (type: {type(level)})")
                    if level<node_level-1:
                        # print('Level up!!')
                        favourite_node = host
                        try:
                            e.add_peer(host)                            
                        except Exception as err1:
                            # print('err1------------------------------')
                            # print(err1)
                            pass
                        node_level = level + 1
                        resp = { "level": node_level, "function": 'map', "gateway": host, "route": [host,] }
                        e.send(host, ujson.dumps(resp))
                if 'function' in msg_json:
                    function = msg_json['function']
                    # print(function)
                    if function == 'ping':
                        try:
                            e.add_peer(host)
                        except Exception as err2:
                            # print('err2------------------------------')
                            # print(err2)
                            pass
                        resp = { "level": node_level, "function": 'pong' }
                        e.send(host, ujson.dumps(resp))
                        e.del_peer(host)
                    
                    elif function == 'route':
                        msg_json['route'].append(long_uid)
                        e.send(favourite_node, ujson.dumps(msg_json))

                peers_table = e.peers_table
                for peer, values in peers_table.items():
                    rssi = values[0]
                    # print(f"Peer {peer}: RSSI = {rssi}")

            except Exception as err:
                # print('err------------------------------')
                # print(err)
                pass



def ping():
    global long_uid
    while True:
        payload = { "ping": long_uid, "level": node_level }
        e.send(peer, ujson.dumps(payload))
        time.sleep(20)


def test_route():
    while True:
        global favourite_node
        global long_uid
        if favourite_node:
            payload = { "function": 'route', "node": long_uid, "route": [long_uid,] }
            # print(payload)
            e.send(favourite_node, ujson.dumps(payload))
            time.sleep(10)


def send_gw(data):
    e.send(favourite_node, data)
    

_thread.start_new_thread(esp_loop, ())
_thread.start_new_thread(ping, ())
_thread.start_new_thread(test_route, ())

print('espnow thread started')

import sys
import uselect

# Create a polling object
spoll = uselect.poll()

# Register sys.stdin for monitoring read events
spoll.register(sys.stdin, uselect.POLLIN)

def read1():
    # Check if data is available and read it if so
    return sys.stdin.read(1) if spoll.poll(0) else None

def read_line():
    # Check if data is available and read it if so
    return sys.stdin.readline() if spoll.poll(0) else None

# buffer = ''
# while True:
    # byte = read1()
    # print(f"Received: {byte} - {type(byte)}")
    
    # if byte is not None:
    #     buffer += byte
    #     print(f"Buffer: {buffer}")
        
    #     # Handle the byte        
    #     if buffer[0]!='{' and buffer[-1:]=='\n':
    #         send_gw(data=buffer.rstrip())
    #         buffer = ''
    #     elif buffer[0]=='{' and buffer[-2:]=='}\n':
    #         send_gw(data=buffer.rstrip())
    #         buffer = ''
    #     else:
    #         ...
    # 
    #    
    # else:
    #     # No data available, continue with other tasks
    #     pass


while True:
    if spoll.poll(0):
        set_led_color((20,0,0))
        time.sleep_ms(50)
        set_led_color((0,0,20))
        rx = sys.stdin.readline().rstrip()     
        msg = rx.decode('utf-8')
        e.send(favourite_node, msg)
