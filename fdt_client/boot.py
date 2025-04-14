# boot.py -- run on boot-up
# List AP and loop to get RSSI + mesh level + number of clients

import network
import sys
import time


wlan = network.WLAN()       # create station interface (the default, see below for an access point interface)
wlan.active(True)           # activate the interface
wlan.scan()                 # scan for access points
# (ssid, bssid, channel, RSSI, security, hidden)
# There are five values for security:
# 0 – open
# 1 – WEP
# 2 – WPA-PSK
# 3 – WPA2-PSK
# 4 – WPA/WPA2-PSK

wlan.isconnected()          # check if the station is connected to an AP
print('connect wlan')
wlan.connect('fas_data') # connect to an AP
time.sleep(2)
print(wlan.config('mac'))          # get the interface's MAC address
print(wlan.ipconfig('addr4'))      # get the interface's IPv4 addresses

# while True:
#     rx = sys.stdin.readline()
    