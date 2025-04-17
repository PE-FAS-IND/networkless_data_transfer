# boot.py -- run on boot-up
# Gateway "futuristic_data_transfer"

import network

ap = network.WLAN(network.WLAN.IF_AP) # create access-point interface
ap.config(ssid='fas_data', password='fas+123') 
# ap.config(max_clients=10)
ap.active(True) 