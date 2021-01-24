import ntptime
import utime


def update_time():
    while True:
        try:
            ntptime.settime()
            break
        except OSError:
            utime.sleep_ms(10)
    print('time:', utime.localtime())
