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

pin = Pin(8, Pin.OUT)   # set GPIO0 to output to drive NeoPixels
np = NeoPixel(pin, 8)   # create NeoPixel driver on GPIO0 for 8 pixels
np[0] = (0, 0, 20) # set the first pixel to white
np.write()

sta = network.WLAN(network.STA_IF)
sta.active(True)
print(sta.config('mac'))

e = espnow.ESPNow()
e.active(True)

node_level = 1000
peer = b'\xbb\xbb\xbb\xbb\xbb\xbb'          # Multiple broadcast
e.add_peer(peer)

favourite_node = None
long_uid = binascii.hexlify(machine.unique_id()).decode('utf-8')

def esp_loop():
    global node_level
    global favourite_node
    global long_uid

    while True:
        host, msg = e.recv()
        if msg:             # msg == None if timeout in recv()
            print(host, msg)
            try:
                msg_json = ujson.loads(msg)
                if 'level' in msg_json:
                    level = msg_json['level']
                    print(f"{host} is level {level} (type: {type(level)})")
                    if level<node_level-1:
                        print('Level up!!')
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
                    print(function)
                    if function == 'ping':
                        try:
                            e.add_peer(host)
                        except Exception as err2:
                            print('err2------------------------------')
                            print(err2)
                            pass
                        resp = { "level": node_level, "function": 'pong' }
                        e.send(host, ujson.dumps(resp))
                        e.del_peer(host)
                    
                    elif function == 'route':
                        msg_json['route'].append(long_uid)
                        e.send(favourite_host, ujson.dumps(msg_json))

                peers_table = e.peers_table
                for peer, values in peers_table.items():
                    rssi = values[0]
                    print(f"Peer {peer}: RSSI = {rssi}")

            except Exception as err:
                print('err------------------------------')
                print(err)
                pass

            if msg == b'end':
                break


def ping():
    while True:
        payload = { "function": 'ping', "level": node_level }
        e.send(peer, ujson.dumps(payload))
        time.sleep(20)


def test_route():
    while True:
        global favourite_node
        if favourite_node:
            payload = { "function": 'route', "node": long_uid, "route": [long_uid,] }
            print(payload)
            e.send(favourite_node, ujson.dumps(payload))
            time.sleep(10)


def send_gw(data):
    global favourite_node
    uid_b = machine.unique_id()
    # uid = binascii.hexlify(uid_b[3:6]).decode('utf-8')
    payload = f"{long_uid}{data}\n"
    print(payload)
    e.send(favourite_node, ujson.dumps(payload))
    

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

buffer = ''
while True:
    byte = read1()
    # print(f"Received: {byte} - {type(byte)}")
    
    if byte is not None:
        buffer += byte
        print(f"Buffer: {buffer}")
        
        # Handle the byte        
        if buffer[0]!='{' and buffer[-1:]=='\n':
            send_gw(data=buffer.rstrip())
            buffer = ''
        elif buffer[0]=='{' and buffer[-2:]=='}\n':
            send_gw(data=buffer.rstrip())
            buffer = ''
        else:
            ...
            
        
    else:
        # No data available, continue with other tasks
        pass