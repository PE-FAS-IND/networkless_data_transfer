from machine import Pin
from neopixel import NeoPixel
import espnow
import network
import binascii
import ujson
import _thread
import sys


def write_serial(data):
    data = data.rstrip().replace("\r\n", "\n")
    sys.stdout.write(f"{data}\r\n")


pin = Pin(8, Pin.OUT)   # set GPIO0 to output to drive NeoPixels
np = NeoPixel(pin, 8)   # create NeoPixel driver on GPIO0 for 8 pixels

def set_led_color(color=(20, 20, 20)):
    np[0] = color # set the first pixel to white
    np.write()

set_led_color(color=(20, 20, 20))

sta = network.WLAN(network.STA_IF)
sta.active(True)
write_serial(sta.config('mac'))

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
            if msg[0] == '{':
                try:
                    msg_json = ujson.loads(msg)
                    write_serial(msg_json)
                    if 'function' in msg_json:
                        function = msg_json['function']
                        write_serial(function)
                        if function == 'ping':
                            e.add_peer(host)
                            resp = { "level": node_level, "function": 'pong' }
                            e.send(host, ujson.dumps(resp))
                            e.del_peer(host)
                        
                        elif function == 'route':
                            msg_json['route'].append(long_uid)
                            write_serial(ujson.dumps(msg_json))

                    peers_table = e.peers_table
                    for peer, values in peers_table.items():
                        rssi = values[0]
                        write_serial(f"Peer {peer}: RSSI = {rssi}")
                except Exception as err:
                    write_serial(err)
                    pass
            else:
                try:
                    # Remove the 'b' prefix manually
                    cleaned_str = msg.decode('utf-8').replace("b'", "").replace("'", "")
                    write_serial(cleaned_str)
                    # Convert the string into bytes and then decode it
                    # decoded_string = bytes(cleaned_str, 'utf-8').decode('unicode-escape')
                    # print(decoded_string)
                except Exception as err3:
                    write_serial(f"err3: {err3}")

            if msg == b'end':
                break

_thread.start_new_thread(espnow_task, ())
