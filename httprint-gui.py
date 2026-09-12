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

import tkinter as tk
import pygame

TMP = tempfile.gettempdir()


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
INSTANCENAME = "HTTPrint"
colors = []
exe = ""
 
key_lookup = ""
keytime = 0

root = None
app = None









# GUI
class FullscreenApp:
    def __init__(self, master, fullscreen=False, keypad=False):
        self.master = master
        self.master.title("HTTPrint")
        try:
            if os.path.exists("httprint.png"):
                self.master.iconphoto(True, tk.PhotoImage(file="httprint.png"))
        except Exception:
            pass
        self.master.configure(background="black")

        self.master.geometry("800x600+100+100")
        self.master.attributes('-fullscreen', fullscreen)

        self.master.bind("<F11>", self.toggle_fullscreen)
        self.master.bind("<Escape>", self.quit_fullscreen)
        self.master.bind('<KeyPress>', self.onKeyPress)
        self.master.bind("<Control-c>", self.quit_app)
        self.master.bind("<KeyPress-q>", self.quit_app)
        self.master.bind("<KeyPress-Q>", self.quit_app)
        self.master.bind("<KeyPress-f>", self.toggle_fullscreen)
        self.master.bind("<KeyPress-F>", self.toggle_fullscreen)
        self.master.bind("<KeyPress-k>", self.toggle_keypad)
        self.master.bind("<KeyPress-K>", self.toggle_keypad)

        self.label = tk.Label(master)
        self.label.configure(bg="black", fg="lightblue")
        self.label.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.label.bind("<Configure>", self.on_window_resize)

        self.text = ""
        self.keypad_frame = None
        self.keypad_visible = False
        if keypad:
            self.create_touch_keypad()
            self.show_keypad()

    def quit_fullscreen(self, event=None):
        self.master.attributes('-fullscreen', False)

    def toggle_fullscreen(self, event=None):
        self.master.attributes('-fullscreen', not  self.master.attributes('-fullscreen'))

    def quit_app(self, event=None):
        self.master.quit()
        self.master.destroy()
        raise SystemExit(0)

    def normalize_key(self, key):
        if key is None:
            return ""
        key = str(key).strip()
        if not key:
            return ""
        normalized = {
            "asterisk": "*",
            "numbersign": "#",
            "hash": "#",
            "multiply": "*",
        }.get(key.lower(), key)
        if normalized.isalpha():
            return normalized.upper()
        return normalized

    def create_touch_keypad(self):
        self.keypad_frame = tk.Frame(self.master, bg="black")
        self.keypad_buttons = []
        self.keypad_frame.bind("<Configure>", self.on_keypad_resize)

        keypad_values = [
            ["1", "2", "3", "A"],
            ["4", "5", "6", "B"],
            ["7", "8", "9", "C"],
            ["*", "0", "#", "D"],
        ]
        for row, keypad_row in enumerate(keypad_values):
            for column, value in enumerate(keypad_row):
                button = tk.Button(
                    self.keypad_frame,
                    text=value,
                    command=lambda v=value: self.simulate_key(v),
                    bg="#101010",
                    fg="lightblue",
                    activebackground="#222222",
                    activeforeground="lightblue",
                    font=("COURIER", 28, "bold"),
                    width=3,
                    height=2,
                    relief="flat",
                )
                button.grid(row=row, column=column, padx=2, pady=2, sticky="nsew")
                self.keypad_buttons.append(button)

        for column in range(4):
            self.keypad_frame.grid_columnconfigure(column, weight=1)
        for row in range(4):
            self.keypad_frame.grid_rowconfigure(row, weight=1)

    def on_keypad_resize(self, event):
        font_size = max(10, int(min(event.width / 16, event.height / 10)))
        for button in self.keypad_buttons:
            button.configure(font=("COURIER", font_size, "bold"))

    def show_keypad(self):
        if self.keypad_frame is None:
            return
        self.keypad_frame.place(relx=0.5, rely=1.0, anchor="s", relwidth=0.5, relheight=0.5)
        self.label.place_configure(relheight=0.5)
        self.keypad_visible = True

    def hide_keypad(self):
        if self.keypad_frame is None:
            return
        self.keypad_frame.place_forget()
        self.label.place_configure(relheight=1.0)
        self.keypad_visible = False

    def toggle_keypad(self, event=None):
        if self.keypad_frame is None:
            self.create_touch_keypad()
        if self.keypad_visible:
            self.hide_keypad()
        else:
            self.show_keypad()

    def simulate_key(self, value):
        global key_lookup
        key_lookup = self.normalize_key(value)

    def update_display(self, text = None):
        if text:
            self.text = text

        s = self.text.splitlines(True)
        le = max([len(line) for line in s])
        ro = len(s)

        width = self.master.winfo_width()
        height = self.master.winfo_height()
        new_font_size = min(int(width / le), int(height / ro / 2))

        self.label.config(text = self.text, font=("COURIER", new_font_size, "bold"))

    def on_window_resize(self, event):
        self.update_display()

    def onKeyPress(self, event=None):
        global key_lookup
        key = event.char if event and event.char else (event.keysym if event else "")
        key_lookup = self.normalize_key(key)





def main(fullscreen=False, keypad=False):
    global root, app, key_lookup, temp_digits, keytime

    logfname = os.path.join(os.path.dirname(os.path.realpath(__file__)),"httprint-gui.log")
    logging.basicConfig(filename=logfname, datefmt='%m/%d/%Y %H:%M:%S', format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)
    # logging.getLogger().addHandler(logging.StreamHandler())

    root = tk.Tk()
    app = FullscreenApp(root, fullscreen=fullscreen, keypad=keypad)

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

    app.master.title(INSTANCENAME)
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
                #keytime = time.time()
                logging.debug ("Reset")
                play("reset")
                displaycode(code)

        # key_lookup = getkey(blocking=False).upper()

        if key_lookup != "":
            # print(key_lookup)
            keytime = time.time()
            if key_lookup in {"Delete", "BackSpace", "Escape"}:
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

        root.update_idletasks()
        root.update()


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
    sound_file = os.path.abspath(os.path.join("sounds", file + ".mp3"))
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
    args = parser.parse_args()
    main(
        fullscreen=args.fullscreen or FULLSCREEN_DEFAULT,
        keypad=args.keypad or KEYPAD_DEFAULT,
    )
