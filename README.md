# Solar Map

I have upgraded an almost 50 year old map of Paris to display solar/lunar positions.

[![Solar/Lunar Map](https://www.marclieser.de/data/content/interests/solarmap/solarmap_ytcue.jpg)](http://www.youtube.com/watch?v=3vjASYzq22o "Solar/Lunar Map")

Since I could not find a (free) web service to query solar and lunar azimuth and elevation, I used equations from [Meeus, Jean. Astronomical Algorithms, 1998](https://shopatsky.com/products/astronomical-algorithms-2nd-edition) and [Astronomy Answers](https://www.aa.quae.nl/en/reken.html) to do the calculations myself.
The accuracy is very poor and there are probably bugs.

The lack of double precision of the ESP8266 means that basic astronomical calculations cannot be performed with the necessary precision.
For example, the Julian day number (JDN) cannot actually be calculated to the day.
I have currently hotfixed this specific problem by breaking the equation into integer and floating point parts, but all following equations lack accuracy and in the long run I will just upgrade to an ESP32.

Next to the solar/lunar map I have added modes to display the current time in the style of an analog clock style and some random animations as well as static ambient lighting.

The map can be controlled from your home wifi through a [web interface](http://solar.marclieser.de/) that has its own [repository](https://github.com/marcwingduck/solar_map_web).

## Components

### Main Components

* [Adafruit HUZZAH ESP8266 Breakout](https://www.adafruit.com/product/2471)
* [Neopixel LEDs (SK6812RGBW)](https://www.adafruit.com/product/2842)

The worst case consumption of the 180 NeoPixels I used for this project is

    4 LEDs (RGBW) x 0.02 A (max current per LED) x 180 NeoPixels = 14.4 A

The ESP8266 consumes up to 250 mA.
So the worst case estimate amounts to 14.65 A, which will never be reached in practice.
Nevertheless, I opted for the next larger power supply (15 A) because it will run cooler as it will never reach its limit and excessive heat could damage the map or dissolve the glue.

So this 15A/5V power supply should be more than enough

* [Power Supply](https://www.meanwell-web.com/en-gb/ac-dc-single-output-enclosed-power-supply-output-rsp--75--5)

### Electronic Components

* 1000 uF capacitor connecting the + and - terminals of the power supply to prevent initial current peaks from damaging other parts of the circuit
* 340 Ohm data line resistor close to the first NeoPixel to help prevent voltage spikes damaging it (see the [Adafruit NeoPixel Überguide](https://learn.adafruit.com/adafruit-neopixel-uberguide/powering-neopixels]), they recommend 300 to 500 Ohm)
* [74AHCT125N](https://www.adafruit.com/product/1787) level-shifter from 3 V board logic to 5 V NeoPixel data signal
* [15 A Fuse](https://www.reichelt.de/feinsicherung-6-3x32mm-flink-us-norm-15a-rnd-170-00087-p204868.html?&nbc=1) and a [Fuse Holder](https://www.reichelt.de/sicherungshalter-6-3-x-32-20-a-32-v-kabel-litt-01550120hxu-p229211.html?&nbc=1)

Of course some cables are required. I soldered the microcontroller and the level-shifter on a prototyping board.

## Configuration

### WiFi Connection

Create a file named `connection` that contains one line `ssid:passwd`. This later enables the project to access the internet in order to retrieve date and time for the solar/lunar position calculations and the clock visualization.

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

## MicroPython Firmware

Download the latest stable [ESP8266 MicroPython firmware](http://micropython.org/download/esp8266/) and create a new Python environment if not done yet:

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

Clear and flash firmware (press/release RESET while holding GPIO0 button to put it into firmware flashing mode)

```
python -m esptool --port /dev/tty.usbserial-XXXXXXXX erase_flash
python -m esptool --port /dev/tty.usbserial-XXXXXXXX --baud 460800 write_flash --flash_size=detect 0 esp8266-20220618-v1.19.1.bin
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

I ran into size issues at some point which could be solved by pre-compiling the scripts into bytecode before transferring them to the ESP8266.

### Get Repository

In order to do so, clone the [MicroPython repository](https://github.com/micropython/micropython).

```
git clone https://github.com/micropython/micropython
```

You should checkout the version according to the firmware you just flashed.

### Build Cross Compiler

```
make -C mpy-cross
```

### Cross Compile Modules

Compile all modules except for the main module:

```
/path/to/mpy-cross/mpy-cross module.py
```

### Transfer Files

Clone WebREPL to have an offline version or use the cached online version:
* [Clone this Repository](https://github.com/micropython/webrepl)
* [Cache this Website](http://micropython.org/webrepl/)

Connect to the MicroPython-XXXXXX WiFi network using the password set or default password `micropythoN`.

Transfer `main.py` and compiled modules as well as the `connection` file to ESP8266 using WebREPL.
