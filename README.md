# httprint-gui

A simple GUI client to pull files from HTTPrint and send them to the printer

## Requirements

* Python3
* CUPS (on linux)
* SumatraPDF (on windows)

## Install

Clone this repo

Copy httprint-gui.conf.sample to httprint-gui.conf and change the settings

To have sounds, copy all [files](https://cloud.cristo.re/s/jfRFeHYKM3pcLPi) into the "sounds" folder and install mpg123

On Windows, download [SumatraPDF](https://www.sumatrapdfreader.org/download-free-pdf-viewer) portable into the script folder

Run: python3 httprint-gui.py

## Command line options

```text
python3 httprint-gui.py [-h] [-f] [-k]

options:
  -h, --help        show this help message and exit
  -f, --fullscreen  start in fullscreen mode
  -k, --k           start with the touch keypad enabled
```

## Keyboard shortcuts

- `F11` or `f`: toggle fullscreen
- `Escape`: exit fullscreen
- `k`: toggle the touch keypad
- `Ctrl+C` or `q`: quit the application

# License and copyright

Copyright 2026 itec <itec@ventuordici.org>


Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Printer icon created by Good Ware - Flaticon
