import machine
from machine import Pin
from neopixel import NeoPixel
import espnow
import network
import binascii
import ujson
import _thread
import sys
import time


def write_serial(data):
    data = data
    sys.stdout.write(f"{data}\r\n")


pin = Pin(8, Pin.OUT)   # set GPIO0 to output to drive NeoPixels
np = NeoPixel(pin, 8)   # create NeoPixel driver on GPIO0 for 8 pixels

def set_led_color(color=(20, 20, 20)):
    np[0] = color # set the first pixel to white
    np.write()

set_led_color(color=(0, 20, 0))

sta = network.WLAN(network.STA_IF)
sta.active(True)

long_uid = binascii.hexlify(machine.unique_id()).decode('utf-8')
write_serial(long_uid)

e = espnow.ESPNow()
e.active(True)
node_level = 0

peer = b'\xbb\xbb\xbb\xbb\xbb\xbb'          # Multiple broadcast
e.add_peer(peer)

data = '{ "level": 0 }'
e.send(peer, data)

def espnow_task():
    global node_level
    while True:
        host, msg = e.recv()
        if msg:
            try:
                msg_json = ujson.loads(msg)
                if 'ping' in msg_json:
                    write_serial(f"ping: {msg_json['ping']}")
                    e.add_peer(host)
                    resp = { "pong": long_uid, "level": node_level }
                    e.send(host, ujson.dumps(resp))
                    e.del_peer(host)
                
                else:
                    write_serial(msg)

            except Exception as err:
                write_serial(f"Erreur = {err}".encode('utf-8'))

_thread.start_new_thread(espnow_task, ())


while True:
    rx = sys.stdin.readline().rstrip()
    if rx is not None:
        try:
            msg_json = ujson.loads(rx)
            if 'dest' in msg_json:
                route = msg_json['route']
                next = route[-1]
                msg_json['route'] = msg_json['route'][0:-1]
                e.add_peer(next)
                e.send(next, ujson.dumps(msg_json))
                e.del_peer(next)

        except Exception as err:
                write_serial(f"Erreur = {err}".encode('utf-8')) 
