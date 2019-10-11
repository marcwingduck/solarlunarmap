# Solar Map

I have Upgraded an almost 50 year old map of Paris to display solar/lunar positions.

![Solar/Luna](http://marclieser.de/data/content/interests/solarmap/solarmap_header.jpg)

## Components

- [ESP8266](https://www.adafruit.com/product/2471)
- [RGBW LED Strips](https://www.adafruit.com/product/2842)
- [Power Supply](https://www.meanwell-web.com/en-gb/ac-dc-single-output-enclosed-power-supply-output-rsp--75--5)

## Build and flash firmware

Detailed description how to setup VM at [Adafruit](https://learn.adafruit.com/building-and-running-micropython-on-the-esp8266/build-firmware#provision-virtual-machine-2-5). When already setup, follow these steps to update and build micropython:

### Start VM

```
cd esp8266-micropython-vagrant
vagrant up
vagrant ssh
```

### Update micropython project

```
cd micropython
git pull --recurse-submodules
make -C mpy-cross
cd ports/esp8266
make
cp build-GENERIC/firmware-combined.bin /vagrant/
exit
vagrant halt
```

### Connect to FTDI, Pins:

```
|                              |
| ( ) (TX) (RX) (C+) ( ) (GND) |
________________________________
```

### Flash

```
esptool.py -p /dev/ttyXXX --baud 460800 write_flash --flash_size=detect 0 firmware-combined.bin
```

### Setup WebREPL

```
screen /dev/ttyXXX 115200
import webrepl_setup
```

Follow setup steps and restart.

## Cross-compile project files

Size of scripts seem to large, so modules need to be cross-compiled:

```
/path/to/mpy-cross/mpy-cross module.py
```

Transfer `main.py` and compiled modules to ESP8266 using webREPL. Remember to replace `mywifi` and `mywifikey` in `main.py`.
