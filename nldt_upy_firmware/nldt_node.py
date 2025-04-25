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
        if msg:
            try:
                msg_json = ujson.loads(msg)
                if 'level' in msg_json:
                    level = msg_json['level']
                    if level<node_level-1:
                        favourite_node = host
                        set_led_color((20,20,20))
                        try:
                            e.add_peer(host)                            
                        except Exception as err1:
                            pass
                        node_level = level + 1
                        # resp = { "level": node_level, "function": 'map', "gateway": host, "route": [host,] }
                        # e.send(host, ujson.dumps(resp))

                if 'ping' in msg_json:
                    write_serial(f"ping: {msg_json['ping']}")
                    e.add_peer(host)
                    resp = { "pong": long_uid, "level": node_level }
                    e.send(host, ujson.dumps(resp))
                    e.del_peer(host)
                
                if 'trace' in msg_json:
                    # e.add_peer(favourite_node)
                    msg_trace = msg_json
                    msg_trace['trace'] = msg_trace['trace'].append(long_uid)
                    e.send(favourite_node, ujson.dumps(msg_trace))

                if 'dest' in msg_json:
                    dest = msg_json['dest']
                    # If node is dest, write serial
                    if dest==long_uid:
                        write_serial(msg)
                    
                    # Else, continue route
                    else:
                        route = msg_json['route']
                        next = route[-1]
                        msg_json['route'] = msg_json['route'][0:-1]
                        e.add_peer(next)
                        e.send(next, ujson.dumps(msg_json))
                        e.del_peer(next)

                else:
                    write_serial(msg)

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

def send_gw(data):
    global favourite_node
    if favourite_node:
        try:
            if data.startswith("b'"):
                data = data[2:-4]
                # print(data)
            payload = ujson.loads(data)

            if "trace" in payload:
                payload["trace"] = [long_uid]

            e.send(favourite_node, ujson.dumps(payload))
        except Exception as err:
            print(err)
        
            
    

_thread.start_new_thread(esp_loop, ())
_thread.start_new_thread(ping, ())

print('espnow thread started')

import sys

while True:
    rx = sys.stdin.readline().rstrip()
    if rx is not None:
        send_gw(rx)
