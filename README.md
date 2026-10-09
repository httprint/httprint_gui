# httprint-gui

A simple GUI client to pull files from HTTPrint and send them to the printer

## Requirements

* Python3
* Pygame (installed from `requirements.txt`)
* CUPS (on linux)
* SumatraPDF (on windows)
* Python dependencies from `requirements.txt`

## Install

Clone this repo

Copy httprint-gui.conf.sample to httprint-gui.conf and change the settings

Install Python dependencies:

```bash
pip install -r requirements.txt
```

On Windows, download [SumatraPDF](https://www.sumatrapdfreader.org/download-free-pdf-viewer) portable into the script folder

To use custom sounds, place MP3 files named `start.mp3`, `fail.mp3`, `reset.mp3`, `print.mp3`, or `button.mp3` in the `sounds/` folder. An alternative sound set is available [at this link](https://cloud.cristo.re/s/jfRFeHYKM3pcLPi).

Run: python3 httprint-gui.py

## Command line options

```text
python3 httprint-gui.py [-h] [-f] [-k] [-s]

options:
  -h, --help        show this help message and exit
  -f, --fullscreen  start in fullscreen mode
  -k, --keypad      start with the touch keypad enabled
  -s, --no-sounds   disable sound playback
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

## Third-party asset licenses

The bundled **Courier Prime Regular** font is from [Courier Prime](https://github.com/quoteunquoteapps/CourierPrime) and is licensed under the SIL Open Font License 1.1. See [assets/OFL-CourierPrime.txt](assets/OFL-CourierPrime.txt) for the full license text.

The bundled arcade sounds in `assets/sounds/` are MP3 conversions of sounds from SubspaceAudio's [512 Sound Effects (8-bit style)](https://opengameart.org/content/512-sound-effects-8-bit-style) collection, released under [CC0](https://creativecommons.org/publicdomain/zero/1.0/). The mappings are: `start.mp3` from `sfx_sound_poweron.wav`, `fail.mp3` from `sfx_sound_shutdown1.wav`, `reset.mp3` from `sfx_sound_noise.wav`, `print.mp3` from `sfx_sound_nagger1.wav`, and `button.mp3` from `sfx_coin_double1.wav`.
