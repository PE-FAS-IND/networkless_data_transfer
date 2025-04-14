import network
import espnow
import sys
import time
import onboard_led

def node():
    # A WLAN interface must be active to send()/recv()
    sta = network.WLAN(network.WLAN.IF_STA)  # Or network.WLAN.IF_AP
    sta.active(True)
    sta.disconnect()      # For ESP8266

    e = espnow.ESPNow()
    e.active(True)

    all_available_peers = b'\xbb\xbb\xbb\xbb\xbb\xbb'   # MAC address of peer's wifi interface
    e.add_peer(all_available_peers)      # Must add_peer() before send()

    # Is_gateway

    # if not -> is_client --> machine id?

    # discovery spam

    # map/remap

    # available routes

    # routes priority

    e.send(all_available_peers, 'mapping', True)

    while True:
        rx = sys.stdin.readline()
        if len(rx)>0:
            e.send(all_available_peers, rx, True)
            # onboard_led.flash(1, 0.1, 1)
