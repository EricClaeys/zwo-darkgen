# ZWO Darkgen

Darkgen is a dark frame library generator for ZWO cameras intended for use with [allsky](https://github.com/thomasjacquin/allsky). It is derived from [zwo-skycam](https://github.com/filiparag/zwo-skycam), an abstration layer for Python [zwoasi](https://github.com/stevemarple/python-zwoasi) binding.

## Installation

This tool was developed on `x86_64` and should run on any posix-like platform for which the ZWO SDK is available, but your mileage may vary.

### Prerequisites

If you are using this with an allsky installation, simply point the tool at the library. Otherwise, fetch the SDK from [ZWO](https://astronomy-imaging-camera.com/software-drivers).

Updating repositories

`sudo apt update`

Git (optional)

`sudo apt -y install git`

Python 3

`sudo apt -y install python3 python3-pip libusb-1.0-0`

Modules

`sudo pip3 install Pillow zwoasi`

### Cloning repository

You can clone this repository by executing:

`git clone https://github.com/ckuethe/zwo-darkgen`

or download the archived repository from GitHub website.

## Usage

```
usage: darkgen.py [-h] [-c CAMERA] [-I] [-l PATH] [-d PATH] [-f STR] [-g MIN:MAX:STEP] [-x MIN:MAX:STEP] [-v] [--flip {n,h,v,hv,vh,b}]
                  [--binning BINNING] [--stack STACK] [--quality QUALITY]

optional arguments:
  -h, --help            show this help message and exit
  -c CAMERA, --camera CAMERA Camera index (default: None)
  -I, --info            Print info about selected camera (default: False)
  -l PATH, --library PATH path to SDK library (default: ./libASICamera2.so)
  -d PATH, --directory PATH path to output darks (default: zwo_dark)
  -f STR, --filename-format STR filename pattern for darks. The tokens {expms}, {gain}, and {temp} will be interpolated as python formats. (default: dark_{expms}ms_{gain:03d}g_{temp:+03d}C.png)
  -g MIN:MAX:STEP, --gain MIN:MAX:STEP gain range to scan (-1=automatic) (default: -1:-1:5)
  -x MIN:MAX:STEP, --exposure MIN:MAX:STEP exposure range to scan, in seconds. (default: 1:120:1)
  -v, --verbose
  --flip {n,h,v,hv,vh,b} flip image: none, horizonal, vertical, both (default: None)
  --binning BINNING     Pixel binning factor (default: 1)
  --stack STACK         Number of exposures to stack to build dark frame (default: 1)
  --quality QUALITY     image quality (default: 100)

When constructing the output filename, the following tokens are available:
{temp} - sensor temperature in C, rounded up: 26.1 -> 27;
{gain} - gain in arbitrary units;
{expms} - exposure time in milliseconds;
{model} - sanitized camera model: 'ZWO ASI120MM Mini' -> 'zwo_asi120mm_mini';
{stack} - stacking factor
```
