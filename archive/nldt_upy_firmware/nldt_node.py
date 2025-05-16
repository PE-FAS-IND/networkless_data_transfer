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
            write_serial(b'<-- msg in\r\n')
            try:
                while msg.startswith("b"):
                    msg = eval(f"{msg}.decode(utf-8)")

                msg_json = ujson.loads(msg)
                if 'level' in msg_json:
                    level = msg_json['level']
                    if level<node_level-1:
                        favourite_node = host
                        try:
                            e.add_peer(host)                            
                        except Exception as err1:
                            pass
                        node_level = level + 1
                        set_led_color((20,20,20))

                elif 'ping' in msg_json:
                    e.add_peer(host)
                    resp = { "pong": long_uid, "level": node_level }
                    e.send(host, ujson.dumps(resp))
                    e.del_peer(host)
                
                elif 'trace' in msg_json:
                    msg_trace = msg_json
                    msg_trace['trace'] = msg_trace['trace'].append(long_uid)
                    e.send(favourite_node, ujson.dumps(msg_trace))

                elif 'dest' in msg_json:
                    dest = msg_json['dest']

                    # If node is dest, write serial
                    if dest==long_uid:
                        write_serial(ujson.dumps(msg_json))
                    
                    # Else, continue route
                    else:
                        route = msg_json['route']
                        next = route[-1]
                        msg_json['route'] = msg_json['route'][0:-1]
                        e.add_peer(next)
                        e.send(next, ujson.dumps(msg_json))
                        e.del_peer(next)

                else:
                    write_serial('No special key found in espnow msg')
                    write_serial(msg_json)

                peers_table = e.peers_table
                for peer, values in peers_table.items():
                    rssi = values[0]
                    # print(f"Peer {peer}: RSSI = {rssi}")

            except Exception as err:
                write_serial('err------------------------------')
                write_serial(err)
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
            while data.startswith("b"):
                data = eval(f"{data}.decode(utf-8)")

            payload = ujson.loads(data)

            if "trace" in payload:
                payload["trace"] = [long_uid]
            e.send(favourite_node, ujson.dumps(payload))

        except Exception as err:
            write_serial('line 129')
            write_serial(data)
            write_serial(err)
        
            
    

_thread.start_new_thread(esp_loop, ())
_thread.start_new_thread(ping, ())

print('espnow thread started')

import sys

while True:
    rx = sys.stdin.readline().rstrip()
    if rx is not None and rx!='\r':
        send_gw(rx)
