#!/usr/bin/env python3
"""
httprint-gui

Copyright 2025 itec <itec@ventuordici.org>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import time
import os
import subprocess
from subprocess import DEVNULL
import logging
import json
import glob
import argparse


import requests
import configparser
import tempfile
import socket

import pygame

TMP = tempfile.gettempdir()
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
SOUND_ASSETS_DIR = os.path.join(ASSETS_DIR, "sounds")
SOUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")
FONT_FILE = os.path.join(ASSETS_DIR, "CourierPrime-Regular.ttf")
ICON_FILE = os.path.join(ASSETS_DIR, "httprint.png")



CODE_DIGITS = 4
temp_digits = 0

PRINT_CMD = "lp -n %(copies)s -o sides=%(sides)s -o media=%(media)s %(colormodel)s -o fit-to-page %(in)s"
PRINT_CMD_WIN = "%(exe)s -print-to-default -print-settings fit,paper=%(paper)s,%(duplex)s,%(color)s,%(copies)sx %(filepath)s"

# Read configuration
config = configparser.ConfigParser()
config.read('httprint-gui.conf')

confmain = config['MAIN']
DEVICENAME = confmain.get('devicename','')
SERVER = confmain.get('server','')
TOKEN = confmain.get('token','')
PRESPOOL = False
FULLSCREEN_DEFAULT = confmain.getboolean('fullscreen', fallback=False)
KEYPAD_DEFAULT = confmain.getboolean('keypad', fallback=False)
SOUNDS_ENABLED = confmain.getboolean('sounds', fallback=True)
INSTANCENAME = "HTTPrint"
colors = []
exe = ""
 
key_lookup = ""
keytime = 0

app = None









# GUI
class FullscreenApp:
    KEYPAD_VALUES = (
        ("1", "2", "3", "A"),
        ("4", "5", "6", "B"),
        ("7", "8", "9", "C"),
        ("*", "0", "#", "D"),
    )

    def __init__(self, fullscreen=False, keypad=False):
        pygame.init()
        pygame.display.set_caption("HTTPrint")
        if os.path.isfile(ICON_FILE):
            pygame.display.set_icon(pygame.image.load(ICON_FILE))
        self.windowed_size = (800, 600)
        self.fullscreen = fullscreen
        self.keypad_visible = keypad
        self.text = ""
        self.screen = self._set_display_mode()
        self.draw()

    def _set_display_mode(self):
        flags = pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE
        size = (0, 0) if self.fullscreen else self.windowed_size
        return pygame.display.set_mode(size, flags)

    def toggle_fullscreen(self):
        if not self.fullscreen:
            self.windowed_size = self.screen.get_size()
        self.fullscreen = not self.fullscreen
        self.screen = self._set_display_mode()

    def toggle_keypad(self):
        self.keypad_visible = not self.keypad_visible
        self.draw()

    def quit_app(self):
        pygame.quit()
        raise SystemExit(0)

    def normalize_key(self, key):
        if key is None:
            return ""
        key = str(key).strip()
        if not key:
            return ""
        if key.isalpha():
            return key.upper()
        return key

    def update_display(self, text=None):
        if text is not None:
            self.text = text
        self.draw()

    def draw(self):
        width, height = self.screen.get_size()
        self.screen.fill((0, 0, 0))
        display_height = height // 2 if self.keypad_visible else height
        lines = self.text.splitlines() or [""]
        metrics_font = pygame.font.Font(FONT_FILE, 100)
        widest_line = max(1, max(metrics_font.size(line)[0] for line in lines))
        scale = min(width * 0.9 / widest_line, display_height * 0.7 / (metrics_font.get_linesize() * len(lines)))
        font = pygame.font.Font(FONT_FILE, max(1, int(100 * scale)))
        line_height = font.get_linesize()
        text_height = line_height * len(lines)
        top = max(0, (display_height - text_height) // 2)
        for index, line in enumerate(lines):
            rendered = font.render(line, True, (173, 216, 230))
            self.screen.blit(rendered, rendered.get_rect(center=(width // 2, top + index * line_height + line_height // 2)))

        if self.keypad_visible:
            self._draw_keypad(width, height)
        pygame.display.flip()

    def _draw_keypad(self, width, height):
        margin = max(4, min(width, height) // 100)
        gap = margin
        keypad_top = height // 2
        button_width = (width - 2 * margin - 3 * gap) // 4
        button_height = (height - keypad_top - 2 * margin - 3 * gap) // 4
        font_size = max(10, min(button_width // 2, button_height // 2))
        font = pygame.font.Font(FONT_FILE, font_size)
        self.keypad_buttons = []

        for row, keypad_row in enumerate(self.KEYPAD_VALUES):
            for column, value in enumerate(keypad_row):
                rect = pygame.Rect(
                    margin + column * (button_width + gap),
                    keypad_top + margin + row * (button_height + gap),
                    button_width,
                    button_height,
                )
                pygame.draw.rect(self.screen, (16, 16, 16), rect)
                label = font.render(value, True, (173, 216, 230))
                self.screen.blit(label, label.get_rect(center=rect.center))
                self.keypad_buttons.append((rect, value))

    def process_events(self):
        global key_lookup
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_app()
            if event.type == pygame.VIDEORESIZE and not self.fullscreen:
                self.windowed_size = event.size
                self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                modifiers = pygame.key.get_mods()
                if event.key == pygame.K_q or (event.key == pygame.K_c and modifiers & pygame.KMOD_CTRL):
                    self.quit_app()
                elif event.key == pygame.K_F11 or event.key == pygame.K_f:
                    self.toggle_fullscreen()
                elif event.key == pygame.K_k:
                    self.toggle_keypad()
                elif event.key == pygame.K_ESCAPE:
                    if self.fullscreen:
                        self.toggle_fullscreen()
                    key_lookup = ""
                elif event.key == pygame.K_BACKSPACE:
                    key_lookup = "BackSpace"
                elif event.key == pygame.K_DELETE:
                    key_lookup = "Delete"
                else:
                    key_lookup = self.normalize_key(event.unicode)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.keypad_visible:
                for rect, value in getattr(self, "keypad_buttons", []):
                    if rect.collidepoint(event.pos):
                        key_lookup = value
                        break





def main(fullscreen=False, keypad=False):
    global app, key_lookup, temp_digits, keytime

    logfname = os.path.join(os.path.dirname(os.path.realpath(__file__)),"httprint-gui.log")
    logging.basicConfig(filename=logfname, datefmt='%m/%d/%Y %H:%M:%S', format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)
    # logging.getLogger().addHandler(logging.StreamHandler())

    app = FullscreenApp(fullscreen=fullscreen, keypad=keypad)

    url = f"{SERVER}/api/serverinfo"
    try:
        response = requests.get(url, timeout=5)
    except requests.exceptions.RequestException as e:
        logging.error("Server connection error")
        play("fail")
        display("Error", "No server")
        return()

    message = response.json().get("message")
    INSTANCENAME = message.get("instance-name")
    CODE_DIGITS = message.get("code-digits")


    play("start")
    logging.info("start")
    logging.info("DEVICENAME: " + DEVICENAME)
    logging.info("SERVER: " + SERVER)
    # logging.info("PRESPOOL: " + str(PRESPOOL))

    pygame.display.set_caption(INSTANCENAME)
    display(INSTANCENAME, DEVICENAME)
    resetdisplay = True
    displaytime = time.time() + 5

    global colors, exe
    if os.name == "posix":
        #search color capabilities
        try:
            col = subprocess.check_output("lpoptions -l | grep ColorModel", shell=True).decode("utf-8").strip()
            col = col.split(":")[1]
            col = col.replace("*","").strip().split(" ")
            if len(col) == 1:
                colors = [col[0], col[0]]
            elif len(col) == 2:
                colgray = [i for i in col if i.lower() in ["gray","grayscale"]][0]
                colcol = [i for i in col if i != colgray][0]
                colors = [colgray, colcol]
        except:
            pass

    elif os.name == "nt":
        exe = glob.glob(os.path.join(os.path.dirname(os.path.realpath(__file__)),"sumatra*.exe"))
        if exe:
            exe = sorted(exe, reverse=True)[0]

    code = ""
    key_lookup = ""
    temp_digits = CODE_DIGITS
    keytime = time.time()

    #loop
    while True:
        time.sleep(0.05)

        if resetdisplay == True and time.time() > displaytime:
            temp_digits = CODE_DIGITS
            resetdisplay = False
            displaycode(code)

        if code != '':
            if time.time() > keytime + 3:
                code = ''
                temp_digits = CODE_DIGITS
                #keytime = time.time()
                logging.debug ("Reset")
                play("reset")
                displaycode(code)

        # key_lookup = getkey(blocking=False).upper()

        if key_lookup != "":
            # print(key_lookup)
            keytime = time.time()
            if key_lookup in {"Delete", "BackSpace"}:
                code = ''
                temp_digits = CODE_DIGITS
                logging.debug ("Reset")
                play("reset")
                displaycode(code)
            # elif key_lookup == "BackSpace": #Used to delete one char
            #     code = code[:-1]
            #     play("button")
            #     displaycode(code)
            elif key_lookup in set("0123456789ABCDabcd*#"):
                key_lookup = key_lookup.upper()
                code += key_lookup
                play("button")

                if code == "ACA": # ACAB easter egg
                    temp_digits = 4
                if code == "*99": # clean queue, only for service
                    subprocess.call("cancel -a -x", shell=True)
                    code = ''
                    logging.debug ("Queue cleaned")
                    play("print")
                if code == "*98": # show ip, only for service
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("1.1.1.1", 80))
                    display("IP",s.getsockname()[0])
                    play("print")
                    code = ''
                    resetdisplay = True
                    temp_digits = CODE_DIGITS
                    displaytime = time.time() + 5
                else:
                    displaycode(code)

            if len(code) == temp_digits:
                logging.debug(code)
                ppdstd = ""
                searchprint(code, ppdstd, PRESPOOL)

                code = ''
                resetdisplay = True
                temp_digits = CODE_DIGITS
                displaytime = time.time() + 5

            key_lookup = ""

        app.process_events()
        app.draw()


def displaycode(code):
    display("Enter code", formatcode(code))

def display(ro1, ro2):
    # print(ro1, ro2)
    r1 = ro1[:16].center(16,' ')
    r2 = ro2[:16].center(16,' ')
    #.write_string(r1 + '\r\n' + r2)
    # print(r1 + ' ' + r2, end="\r")
    text = r1 + '\n' + r2
    if app is not None:
        app.update_display(text)

def formatcode(code):
    ccode = code + "_"*(temp_digits - len(code))
    if temp_digits == 6:
        return '-'.join((ccode[:3], ccode[3:]))
    else:
        return(ccode)

def play(file):
    if not SOUNDS_ENABLED:
        return

    sound_file = os.path.join(SOUND_DIR, file + ".mp3")
    if not os.path.isfile(sound_file):
        sound_file = os.path.join(SOUND_ASSETS_DIR, file + ".mp3")
    if not os.path.isfile(sound_file):
        return

    try:
        if not pygame.get_init():
            pygame.mixer.init()
        sound = pygame.mixer.Sound(sound_file)
        sound.play()
    except Exception:
        pass


def searchprint(code, ppdstd, ps):

    logging.info ("Searching " + code)
    display("Searching...", "")

    url = f"{SERVER}/api/download/{code}?token={TOKEN}"
    if ps:
        url = f"{url}&ppdstd={ppdstd}"

    try:
        response = requests.get(url, timeout=5)
    except requests.exceptions.RequestException as e:
        logging.error("Server connection error")
        play("fail")
        display("Error", "No server")
        return()

    if 'application/json' in response.headers.get('Content-Type', ''):
        jsonResponse = response.json()
        if jsonResponse["error"]:
            logging.error ("Error" + jsonResponse["message"])
            play("fail")
            display("Error", jsonResponse["message"])
            return()

    elif not 'application/octet-stream' in response.headers.get('Content-Type', ''):
        play("fail")
        display("Error", "Bad header")
        return()

    fname = response.headers['Content-Disposition'].split("filename=")[1]
    tfname = os.path.join(TMP, fname)
    with open(tfname, 'wb') as f:
        f.write(response.content)
    printconf = json.loads(response.headers['Printconf'])

    name = printconf.get("name",os.path.splitext(fname.replace(code + "-",""))[0])
    copies = printconf.get("copies", 1)
    sides = printconf.get("sides", "two-sided-long-edge")
    media = printconf.get("media", "A4")
    color = strbool(printconf.get("color", False))

    logging.info ("Printing " + os.path.basename(tfname))
    play("print")
    display("Printing", name)

    #print
    if os.name == "posix":
        colormodel = ""
        if colors:
            colormodel = colors[0] if not color else colors[1]
            colormodel = "-o ColorModel=" + colormodel
        cmd = PRINT_CMD.split(' ')
        cmd = [x % {'in': tfname, 'copies': copies, 'sides': sides, 'media': media, 'colormodel': colormodel} for x in cmd]
        cmd = " ".join(cmd)

    elif os.name == "nt":
        dsides = {"one-sided":"simplex", "two-sided-long-edge":"duplexlong", "two-sided-short-edge":"duplexshort"}
        duplex = dsides[sides]
        vcolor = "color" if color else "monochrome"

        cmd = PRINT_CMD_WIN.split(' ')
        cmd = [x % {'exe': exe, 'filepath': tfname, 'copies': copies, 'duplex': duplex, 'paper': media, 'color': vcolor} for x in cmd]
        cmd = " ".join(cmd)

    logging.debug(cmd)
    subprocess.call(cmd, shell=True, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL)
    os.remove(tfname)

def strbool(s):
    return s.lower() in ('true', '1', 't', 'y', 'yes')



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HTTPrint GUI client")
    parser.add_argument(
        "-f",
        "--fullscreen",
        action="store_true",
        help="start in fullscreen mode",
    )
    parser.add_argument(
        "-k",
        "--keypad",
        dest="keypad",
        action="store_true",
        help="start with the touch keypad enabled",
    )
    parser.add_argument(
        "-s",
        "--no-sounds",
        action="store_true",
        help="disable sound playback",
    )
    args = parser.parse_args()
    if args.no_sounds:
        SOUNDS_ENABLED = False
    main(
        fullscreen=args.fullscreen or FULLSCREEN_DEFAULT,
        keypad=args.keypad or KEYPAD_DEFAULT,
    )
