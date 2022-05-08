# ZWO Darkgen

Darkgen is a dark frame library generator for ZWO cameras intended for use with [allsky](https://github.com/thomasjacquin/allsky). It is derived from [zwo-skycam](https://github.com/filiparag/zwo-skycam), an abstration layer for Python [zwoasi](https://github.com/stevemarple/python-zwoasi) binding.

## Installation

This tool was developed on `x86_64` and should run on any posix-like platform for which the ZWO SDK is available, but your mileage may vary.

### Prerequisites

If you are using this with an allsky installation, simply point the tool at the library. Otherwise, fetch the SDK from [ZWO](https://astronomy-imaging-camera.com/software-drivers).

Install dependencies from the package repositories:
`sudo apt -y install python3 python3-pip python3-pil python3-numpy libusb-1.0-0`

Install the ZWO ASI library binding
`sudo -H pip3 install zwoasi`

<!--
### Cloning repository

You can clone this repository by executing:

`git clone https://github.com/EricClaeys/zwo-darkgen`

or download the [code archive](https://github.com/ckuethe/zwo-darkgen/archive/refs/heads/master.zip) from GitHub
-->

## Usage

```
darkgen.py [-h] [-I] [-v] [-c CAMERA] [-l PATH] [-d PATH] [-f STR]
           [-g MIN:MAX:STEP] [-x MIN:MAX:STEP] [--binning INT]
           [--flip {n,h,v,hv,vh,b}] [--stack INT] [--quality INT]
           [--offset INT] [--wbr FLOAT] [--wbb FLOAT]
```

### optional arguments:
| Short | Long | Description|
| --- | --- | ---|
| -h | --help | show this help message and exit |
| -I | --info | Print info about selected camera and exit (`False`) |
| -c CAMERA | --camera CAMERA | Camera index (`None`) |
| -l PATH | --library PATH | path to SDK library (`./libASICamera2.so`) |
| -d PATH | --directory PATH | path to output darks (`darks`) |
| -f STR | --filename-format STR | filename pattern for darks.  (`dark_{exps}s_{gain:03d}g_{temp:+02d}C.png`) |
| -g MIN:MAX:STEP | --gain MIN:MAX:STEP | gain range to scan, specified as 3 floats. The value `-1.0` for any of the fields signals that this field should be automatically chosen (`-1.0:-1.0:-1.0`) |
| -x MIN:MAX:STEP | --exposure MIN:MAX:STEP | exposure range to scan, in seconds, specified as 3 integers. (`2:20:2`) |
| -v | --verbose | Increase debug level |
| | --flip {n,h,v,hv,vh,b} | whether the image is to be flipped on the horizonal or vertical axes, or both (`none`) |
| | --binning INT | Pixel binning factor (`1`) |
| | --stack INT | Number of exposures to stack to build dark frame (`1`) |
| | --quality INT | image quality (`100`)
| | --offset INT | brightness offset (`0`)
| | --wbr INT | white balance:red (`None`)
| | --wbb INT | white balance:blue (`None`)


When constructing the output filename, the following tokens are available to be interpolated as python formats.

* `{temp}` - sensor temperature in C, rounded up (eg. 26.1&deg;C -> 27&deg;C)
* `{gain}` - gain in arbitrary units
* `{expms}` - exposure time in milliseconds
* `{model}` - sanitized camera model (eg. `ZWO ASI120MM Mini` -> `zwo_asi120mm_mini`)
* `{stack}` - stacking factor

