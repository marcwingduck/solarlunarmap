import machine
import network
import ntptime
import utime

import paris


def connect():
    try:
        wifi_file = open('connection', 'r')
    except OSError:
        return False

    connection = wifi_file.readline().strip()
    ssid, passwd = connection.split(':')

    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(ssid, passwd)
        deadline = utime.ticks_add(utime.ticks_ms(), 10000)
        while not sta_if.isconnected():
            machine.idle()
            if utime.ticks_diff(deadline, utime.ticks_ms()) < 0:
                break
        else:
            print('network config:', sta_if.ifconfig())
    return sta_if.isconnected()


def set_time():
    while True:
        try:
            ntptime.settime()
            break
        except OSError:
            utime.sleep_ms(10)
    print('time:', utime.localtime())


def init():
    machine.freq(160000000)
    if connect():
        set_time()
        return True
    return False


if __name__ == '__main__':
    is_online = init()
    ap_if = network.WLAN(network.AP_IF)
    if is_online:
        ap_if.active(False)
    else:
        ap_if.active(True)
    paris.run(is_online)
