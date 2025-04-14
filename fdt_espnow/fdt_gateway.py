from machine import Pin
from neopixel import NeoPixel
import espnow
import network
import binascii
import ujson
import _thread

pin = Pin(8, Pin.OUT)   # set GPIO0 to output to drive NeoPixels
np = NeoPixel(pin, 8)   # create NeoPixel driver on GPIO0 for 8 pixels
np[0] = (20, 20, 0) # set the first pixel to white
np.write()           

sta = network.WLAN(network.STA_IF)
sta.active(True)
print(sta.config('mac'))

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
        if msg:             # msg == None if timeout in recv()
            # print(host, msg)
            if msg[0] == '{':
                try:
                    msg_json = ujson.loads(msg)
                    print(msg_json)
                    if 'function' in msg_json:
                        function = msg_json['function']
                        print(function)
                        if function == 'ping':
                            e.add_peer(host)
                            resp = { "level": node_level, "function": 'pong' }
                            e.send(host, ujson.dumps(resp))
                            e.del_peer(host)
                        
                        elif function == 'route':
                            msg_json['route'].append(long_uid)
                            print(ujson.dumps(msg_json))

                    peers_table = e.peers_table
                    for peer, values in peers_table.items():
                        rssi = values[0]
                        print(f"Peer {peer}: RSSI = {rssi}")
                except Exception as err:
                    print(err)
                    pass
            else:
                try:
                    # Remove the 'b' prefix manually
                    cleaned_str = msg.decode('utf-8').replace("b'", "").replace("'", "")
                    print(cleaned_str)
                    # Convert the string into bytes and then decode it
                    # decoded_string = bytes(cleaned_str, 'utf-8').decode('unicode-escape')
                    # print(decoded_string)
                except Exception as err3:
                    print(f"err3: {err3}")

            if msg == b'end':
                break

_thread.start_new_thread(espnow_task, ())
