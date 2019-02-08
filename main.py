import machine
import network
import ntptime
import utime

import paris


def connect():
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.active(True)
        wlan.connect('mywifi', 'mywifikey')
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())


def set_time():
    while True:
        try:
            ntptime.settime()
            break
        except OSError:
            utime.sleep_ms(10)
    print(utime.localtime())


def init():
    machine.freq(160000000)
    connect()
    set_time()


init()
paris.run()
