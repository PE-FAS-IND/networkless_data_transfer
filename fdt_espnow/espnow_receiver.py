import network
import espnow
import binascii
import onboard_led



def gateway():
    # A WLAN interface must be active to send()/recv()
    sta = network.WLAN(network.WLAN.IF_STA)
    sta.active(True)
    sta.disconnect()   # Because ESP8266 auto-connects to last Access Point

    e = espnow.ESPNow()
    e.active(True)

    while True:
        host_b, msg = e.recv()
        host = binascii.hexlify(host_b).decode()
        revert = binascii.unhexlify(host)
        msg = eval(f"{msg}.decode('utf-8')")
        print(msg)
        