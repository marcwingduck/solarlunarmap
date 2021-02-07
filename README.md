# Solar Map

I have upgraded an almost 50 year old map of Paris to display solar/lunar positions.

![Solar/Luna](http://marclieser.de/data/content/interests/solarmap/solarmap_header.jpg)

Since I could not find a web service to query solar and lunar azimuth and elevation, I used the equations from Wikipedia to do the calculations myself.
So there are probably some bugs.

Next to the solar/lunar map I have added modes to display the current time and some random animations.

The map can be controlled from your home wifi through a [web interface](http://solar.marclieser.de/) that has its own [repository](https://github.com/marcwingduck/solar_map_web).

## Components

- [Adafruit HUZZAH ESP8266 Breakout](https://www.adafruit.com/product/2471)
- [Neopixel LEDs (SK6812RGBW)](https://www.adafruit.com/product/2842)
- [Sufficient Power Supply](https://www.meanwell-web.com/en-gb/ac-dc-single-output-enclosed-power-supply-output-rsp--75--5)

## MicroPython Firmware

Download the latest stable firmware from [http://micropython.org/download/esp8266/] and create a new Python environment if not done yet:

```
conda create -n esp python=3.8.3
conda activate esp
pip install esptool
```

Connect an USB RS232 adapter to the HUZZAH ESP8266:

```
|                              |
| ( ) (TX) (RX) (C+) ( ) (GND) |
________________________________
```

Clear and flash firmware

```
esptool.py --port /dev/tty.usbserial-XXXXXXXX erase_flash
esptool.py --port /dev/tty.usbserial-XXXXXXXX --baud 460800 write_flash --flash_size=detect 0 esp8266-20210202-v1.14.bin
```

Keep the USB connection for the next step.

## WebREPL Setup

Open emulated terminal and initiate the setup process while still being connected to the USB RS232 adapter:

```
screen /dev/tty.usbserial-XXXXXXXX 115200
import webrepl_setup
```

Follow setup steps and restart.

## Cross-compile Project Files

The size of scripts seem too large, so modules need to be pre-compiled into bytecode.

### Get Repository

In order to do so, clone the [MicroPython repository](https://github.com/micropython/micropython).


```
git clone https://github.com/micropython/micropython --recurse-submodules
```

Checkout the version according to the firmware you just flashed:

```
cd micropython
git checkout v1.14
```

### Build Cross Compiler

```
make -C mpy-cross
cd ports/esp8266
make
```

### Cross Compile Modules

Compile all modules except for the main module:

```
/path/to/mpy-cross/mpy-cross module.py
```

### Transfer Files

Clone WebREPL to have an offline version or use the cached online version:
* [Repository](https://github.com/micropython/webrepl)
* [Website](http://micropython.org/webrepl/)

Connect to the MicroPython-XXXXXX WiFi network using the password set or default password micropythoN.

Transfer `main.py` and compiled modules to ESP8266 using WebREPL.

## Configuration

### WiFi Connection

Create and move a file named `connection` that contains one line `ssid:passwd` using WebREPL to enable the project to access the internet in order to retrieve date and time.

### Frame Constants

Variables in `paris.py` that need to be adjusted according to your frame.

The number of LEDs

```
n = 180
```

The number of horizontal (cols) and vertical LEDs (rows)

```
cols = 54
rows = 36
```

The number of LEDs per centimeter

```
leds_per_cm = 0.6
```

Latitude and longitude of the location in degrees

```
coords = (48.860536, 2.332237)
```