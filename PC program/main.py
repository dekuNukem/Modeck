import os
import sys
import time
import random
import webbrowser
import configparser
import irc_bot_noblock
from tkinter import *
from helpers import *

MAIN_WINDOW_WIDTH = 600
MAIN_WINDOW_HEIGHT = 500
EEPROM_BACKLIGHT_ADDR = 10
key_list = [('none', 0), ('left control', 128), ('left shift', 129), ('left alt', 130), ('Mac left command', 131), ('right control', 132), ('right shift', 133), ('right alt', 134), ('Mac right command', 135), ('up arrow', 218), ('down arrow', 217), ('left arrow', 216), ('right arrow', 215), ('backspace', 178), ('tab', 179), ('return', 176), ('esc', 177), ('insert', 209), ('delete', 212), ('page up', 211), ('page down', 214), ('home', 210), ('end', 213), ('capslock', 193), ('f1', 194), ('f2', 195), ('f3', 196), ('f4', 197), ('f5', 198), ('f6', 199), ('f7', 200), ('f8', 201), ('f9', 202), ('f10', 203), ('f11', 204), ('f12', 205), (' ', 32), ("'", 39), (',', 44), ('-', 45), ('.', 46), ('/', 47), ('0', 48), ('1', 49), ('2', 50), ('3', 51), ('4', 52), ('5', 53), ('6', 54), ('7', 55), ('8', 56), ('9', 57), (';', 59), ('=', 61), ('[', 91), ('\\', 92), (']', 93), ('`', 96), ('a', 97), ('b', 98), ('c', 99), ('d', 100), ('e', 101), ('f', 102), ('g', 103), ('h', 104), ('i', 105), ('j', 106), ('k', 107), ('l', 108), ('m', 109), ('n', 110), ('o', 111), ('p', 112), ('q', 113), ('r', 114), ('s', 115), ('t', 116), ('u', 117), ('v', 118), ('w', 119), ('x', 120), ('y', 121), ('z', 122)]
key_dict = dict(key_list)

# remember to add version number in eeprom and config file

root = Tk()
root.title("modeck")
root.geometry(str(MAIN_WINDOW_WIDTH) + "x" + str(MAIN_WINDOW_HEIGHT))
root.resizable(width=FALSE, height=FALSE)
panel_bg = PhotoImage(file = local_file("bg.pbm"))
knob_img_list = [PhotoImage(file="knob_small_1.gif"), PhotoImage(file="knob_small_2.gif"), PhotoImage(file="knob_small_3.gif"), PhotoImage(file="knob_small_4.gif"), PhotoImage(file="knob_small_5.gif")]
ts_img_list = [PhotoImage(file="toggle_down.pbm"), PhotoImage(file="toggle_up.pbm")]
green_light = PhotoImage(file="gl.pbm")
button_img_list = [PhotoImage(file="unpressed.pbm"), PhotoImage(file="pressed.pbm")]
chat_channel = ''
owner_oauth = ''
owner_username = ''
chat_bot = None
panel = panel_status()
window_count = 0
config_filename = 'modeck_settings.txt'
parser = configparser.ConfigParser()
parser.read(config_filename)
needs_update = 0
main_canvas = Canvas(root, width=MAIN_WINDOW_WIDTH, height=MAIN_WINDOW_HEIGHT)
rotary_sw0_dispatch = None

def gui_update_non_block():
    root.update()
    root.update_idletasks()

def serial_init():
    serial_find_frame = Frame(root)
    serial_find_frame.pack(fill=BOTH, expand=1)
    text_head = Label(serial_find_frame, text="Looking for the device...")
    text_head.place(x=200, y=20)
    gui_update_non_block()
    while 1:
        device_port = find_device()
        if device_port != '':
            print("device found!")
            serial_find_frame.destroy()
            return device_port
        text_status = Label(serial_find_frame, text="device not found, please connect the cable")
        text_status.place(x=200, y= 200)
        gui_update_non_block()

def draw_knob(master, x, y, state, tag):
    master.delete(tag)
    master.create_image(x, y, image=knob_img_list[state], tag=tag)
    gui_update_non_block()

def draw_toggle_switch(master, x, y, state, tag):
    master.delete(tag)
    master.create_image(x, y, image=ts_img_list[state], tag=tag)
    if state == 1:
        master.create_image(x, y - 50, image=green_light, tag=tag)
    gui_update_non_block()

def draw_button(master, x, y, state, tag):
    master.delete(tag)
    master.create_image(x, y, image=button_img_list[state], tag=tag)
    gui_update_non_block()

def try_login(auto=False):
    section_name = "Login_info"
    global owner_username, owner_oauth, chat_channel, parser
    def login_check():
        nonlocal done, login_frame
        global owner_username, owner_oauth, chat_channel, chat_server_list, chat_bot
        owner_username = username_textbox.get().lower().replace(" ", '')
        owner_oauth = oauth_textbox.get().replace(" ", '')
        if not owner_oauth.startswith("oauth:"):
            owner_oauth = 'oauth:' + owner_oauth
        chat_channel = channel_textbox.get().lower().replace(" ", '')
        channel_check_label = Label(login_frame, text="Checking " + chat_channel + " channel properties...")
        channel_check_label.pack()
        gui_update_non_block()
        chat_server_list = channel_type_check(chat_channel)
        if len(chat_server_list) <= 0:
            err_label = Label(login_frame, text="Channel " + '"' + chat_channel + '"' + " doesn't seem to exist on twitch, try again.")
            err_label.pack()
            return
        hold_on_label = Label(login_frame, text="Trying to connect to " + chat_channel + "...")
        hold_on_label.pack()
        gui_update_non_block()
        chat_server = random.choice(chat_server_list)
        chat_server = [chat_server.split(":")[0], int(chat_server.split(":")[1])]
        chat_bot = irc_bot_noblock.irc_bot(owner_username, owner_oauth, chat_channel, chat_server[0], chat_server[1], timeout = 330, commands = 1)
        while 1:
            lol = chat_bot.retry_connect(auto_retry=False)
            result = lol[0]
            info = lol[1]
            if result == 'login error':
                login_err_label = Label(login_frame, text="Unable to log into twitch chat, is your username and OAuth correct?")
                login_err_label.pack()
                return
            if result == 'login error':
                login_err_label = Label(login_frame, text="Login exception: " + info + ", retrying...")
                login_err_label.pack()
                return
            if result == 'success':
                break
        if not parser.has_section(section_name):
            parser.add_section(section_name)
        parser.set(section_name, "owner_username", str(owner_username))
        parser.set(section_name, "chat_channel", str(chat_channel))
        parser.set(section_name, "owner_oauth", str(owner_oauth))
        dump_config(parser, config_filename)
        done = True

    def callback(event):
        webbrowser.open_new(r"http://www.twitchapps.com/tmi")

    def cancel_window():
        nonlocal done
        if auto == True:
            root.destroy()
            exit()
        done = True

    done = False

    login_frame = Frame(root)
    login_frame.pack(fill=BOTH, expand=1)
    username_label = Label(login_frame, text="Your Twitch username:")
    username_textbox = Entry(login_frame)

    channel_label = Label(login_frame, text="The Twitch channel you wish to join:")
    channel_textbox = Entry(login_frame)

    oauth_instruction_label = Label(login_frame, text="Your OAuth key. If you don't already have one, click the url below to get one.")
    oauth_label = Label(login_frame, text="www.twitchapps.com/tmi", fg="blue", cursor="hand2")
    oauth_textbox = Entry(login_frame)
    
    submit_button = Button(login_frame, text ="Submit", command = login_check)
    cancel_button = Button(login_frame, text ="Cancel", command = cancel_window)

    try:
        owner_username = parser[section_name]['owner_username']
        chat_channel = parser[section_name]['chat_channel']
        owner_oauth = parser[section_name]['owner_oauth']
    except Exception as e:
        print("Exception loading login info from parser: " + str(e))
        
    username_textbox.insert(END, owner_username)
    channel_textbox.insert(END, chat_channel)
    oauth_textbox.insert(END, owner_oauth)
    username_label.pack()
    username_textbox.pack()
    channel_label.pack()
    channel_textbox.pack()
    oauth_instruction_label.pack()
    oauth_label.pack()
    oauth_textbox.pack()
    submit_button.pack()
    cancel_button.pack()
    oauth_label.bind("<Button-1>", callback)
    if auto and owner_oauth != '':
        login_check()
    while 1:
        gui_update_non_block()
        if done:
            login_frame.destroy()
            return

def draw_panel(canvas):
    draw_knob(canvas, 301, 156, panel.rotary_sw0_position, "knob_slow")
    draw_knob(canvas, 221, 365, panel.rotary_sw1_position, "knob_ad")
    draw_toggle_switch(canvas, 99, 135, panel.toggle_sw0_position, "ts_sub")
    draw_toggle_switch(canvas, 508, 75, panel.toggle_sw1_position, "ts_cust")
    draw_button(canvas, 80, 340, panel.button0_status, "button_0")
    draw_button(canvas, 510, 185, panel.button1_status, "button_1")
    draw_button(canvas, 391, 270, panel.button2_status, "button_2")
    draw_button(canvas, 510, 270, panel.button3_status, "button_3")
    draw_button(canvas, 391, 360, panel.button4_status, "button_4")
    draw_button(canvas, 510, 360, panel.button5_status, "button_5")

def bl_settings():
    global window_count
    def quit_win():
        global window_count
        bl_window.destroy()
        window_count -= 1
    def sss(event):
        print(brightness_slider.get())
        setbacklight(ser, brightness_slider.get())
    if window_count >= 1:
        print("too many windows")
        return
    bl_window = Toplevel(root)
    bl_window.title('Button Backlight')
    bl_window.geometry('200x60')
    bl_window.resizable(width=FALSE, height=FALSE)
    bl_window.protocol("WM_DELETE_WINDOW", quit_win)
    brightness_slider = Scale(bl_window, from_=0, to=255, orient=HORIZONTAL, command=sss)
    brightness_slider.set(eepread(ser, EEPROM_BACKLIGHT_ADDR))
    brightness_slider.pack()
    bl_window.focus_set()
    window_count += 1

def dump_config(con, filename):
    with open(filename, 'w') as configfile:
        con.write(configfile)

def button_custom(index):
    global window_count
    
    section_name = "Pushbutton " + str(index)

    def quit_win():
        global window_count
        button_window.destroy()
        window_count -= 1

    def ok():
        global needs_update
        eep_addr_start = (index + 2) * 10

        selected = r_var.get()

        key0 = drop_var0.get()
        key1 = drop_var1.get()
        key2 = drop_var2.get()
        key3 = drop_var3.get()
        chat_command = chat_msg_textbox.get()
        button_nickname = button_nickname_textbox.get()

        if not parser.has_section(section_name):
            parser.add_section(section_name)
        parser.set(section_name, "radiobutton_position", str(selected))
        parser.set(section_name, "hotkey0", str(key0))
        parser.set(section_name, "hotkey1", str(key1))
        parser.set(section_name, "hotkey2", str(key2))
        parser.set(section_name, "hotkey3", str(key3))
        parser.set(section_name, "chat_command", str(chat_command))
        parser.set(section_name, "button_nickname", str(button_nickname))

        if selected != 1:
            eepwrite(ser, eep_addr_start+9, 0)
        else:
            for i in range(10):
                eepzero(ser, eep_addr_start+i)
            eepwrite(ser, eep_addr_start, key_dict[key0])
            eepwrite(ser, eep_addr_start+1, key_dict[key1])
            eepwrite(ser, eep_addr_start+2, key_dict[key2])
            eepwrite(ser, eep_addr_start+3, key_dict[key3])
            eepwrite(ser, eep_addr_start+9, 1)

        dump_config(parser, config_filename)
        needs_update = 1
        quit_win()

    if window_count >= 1:
        print("too many windows")
        return
    button_window = Toplevel(root)
    button_window.title("Button " + str(index) + " Settings")
    button_window.geometry('600x230')
    button_window.resizable(width=FALSE, height=FALSE)
    button_window.protocol("WM_DELETE_WINDOW", quit_win)

    radiobutton_position_prev = 0
    key0_prev = 'none'
    key1_prev = 'none'
    key2_prev = 'none'
    key3_prev = 'none'
    chat_command_prev = ''
    button_nickname_prev = ''
    try:
        radiobutton_position_prev = int(parser[section_name]['radiobutton_position'])
        key0_prev = parser[section_name]['hotkey0']
        key1_prev = parser[section_name]['hotkey1']
        key2_prev = parser[section_name]['hotkey2']
        key3_prev = parser[section_name]['hotkey3']
        chat_command_prev = parser[section_name]['chat_command']
        button_nickname_prev = parser[section_name]['button_nickname']
    except Exception as e:
        print("exception loading button setting: " + str(e))
        pass

    r_var = IntVar()
    R0 = Radiobutton(button_window, text="Not used", variable=r_var, value=0)
    R1 = Radiobutton(button_window, text="Use this button as keyboard hotkey", variable=r_var, value=1)
    R2 = Radiobutton(button_window, text="Use this button for chat command", variable=r_var, value=2)
    r_var.set(radiobutton_position_prev)
    R0.place(x=10, y=5)
    R1.place(x=10, y=40)
    R2.place(x=10, y=110)
    
    OPTIONS = [x[0] for x in key_list]
    drop_var0 = StringVar(button_window)
    drop_var0.set(OPTIONS[OPTIONS.index(key0_prev)])
    hotkey_dropdown0 = OptionMenu(button_window, drop_var0, *OPTIONS)
    hotkey_dropdown0.config(width=15)
    hotkey_dropdown0.place(x=10, y=70)

    drop_var1 = StringVar(button_window)
    drop_var1.set(OPTIONS[OPTIONS.index(key1_prev)])
    hotkey_dropdown1 = OptionMenu(button_window, drop_var1, *OPTIONS)
    hotkey_dropdown1.config(width=15)
    hotkey_dropdown1.place(x=155, y=70)

    drop_var2 = StringVar(button_window)
    drop_var2.set(OPTIONS[OPTIONS.index(key2_prev)])
    hotkey_dropdown2 = OptionMenu(button_window, drop_var2, *OPTIONS)
    hotkey_dropdown2.config(width=15)
    hotkey_dropdown2.place(x=300, y=70)

    drop_var3 = StringVar(button_window)
    drop_var3.set(OPTIONS[OPTIONS.index(key3_prev)])
    hotkey_dropdown3 = OptionMenu(button_window, drop_var3, *OPTIONS)
    hotkey_dropdown3.config(width=15)
    hotkey_dropdown3.place(x=445, y=70)

    confirm_button = Button(button_window, text ="Confirm", command = ok)
    confirm_button.place(x=510, y=200)

    plus = Label(button_window, text="+")
    plus.place(x=144, y = 72)
    plus1 = Label(button_window, text="+")
    plus1.place(x=289, y = 72)
    plus2 = Label(button_window, text="+")
    plus2.place(x=434, y = 72)

    chat_msg_textbox = Entry(button_window)
    chat_msg_textbox.place(x=15, y=140)
    chat_msg_textbox.configure(width=50)
    chat_msg_textbox.insert(END, chat_command_prev)

    ask_nickname = Label(button_window, text="Button Name: ")
    ask_nickname.place(x=15, y = 174)

    button_nickname_textbox = Entry(button_window)
    button_nickname_textbox.place(x=15, y=195)
    button_nickname_textbox.configure(width=20)
    button_nickname_textbox.insert(END, button_nickname_prev)

    button_window.focus_set()
    window_count += 1
    
def slowmode_settings():
    global window_count

    section_name = "Slowmode"

    def draw_error():
        err_label = Label(slowmode_window, text="Please enter a positive number")
        err_label.pack()
    def quit_win():
        global window_count
        slowmode_window.destroy()
        window_count -= 1
    def ok():
        if not parser.has_section(section_name):
            parser.add_section(section_name)
        val_pos1 = pos1_textbox.get()
        val_pos2 = pos2_textbox.get()
        val_pos3 = pos3_textbox.get()
        val_pos4 = pos4_textbox.get()
        if not (is_int(val_pos1) and is_int(val_pos2) and is_int(val_pos3) and is_int(val_pos4)):
            draw_error()
            return
        parser.set(section_name, "slow_position_1", str(val_pos1))
        parser.set(section_name, "slow_position_2", str(val_pos2))
        parser.set(section_name, "slow_position_3", str(val_pos3))
        parser.set(section_name, "slow_position_4", str(val_pos4))
        dump_config(parser, config_filename)
        quit_win()
        
    if window_count >= 1:
        print("too many windows")
        return
    slowmode_window = Toplevel(root)
    slowmode_window.title('Slowmode setting')
    slowmode_window.geometry('300x250')
    slowmode_window.resizable(width=FALSE, height=FALSE)
    slowmode_window.protocol("WM_DELETE_WINDOW", quit_win)
    pos1_label = Label(slowmode_window, text="Position 1: ")
    pos2_label = Label(slowmode_window, text="Position 2: ")
    pos3_label = Label(slowmode_window, text="Position 3: ")
    pos4_label = Label(slowmode_window, text="Position 4: ")

    pos1_textbox = Entry(slowmode_window)
    pos2_textbox = Entry(slowmode_window)
    pos3_textbox = Entry(slowmode_window)
    pos4_textbox = Entry(slowmode_window)

    confirm_button = Button(slowmode_window, text ="Confirm", command = ok)

    val_pos1_prev = '3'
    val_pos2_prev = '5'
    val_pos3_prev = '10'
    val_pos4_prev = '30'
    try:
        val_pos1_prev = parser[section_name]['slow_position_1']
        val_pos2_prev = parser[section_name]['slow_position_2']
        val_pos3_prev = parser[section_name]['slow_position_3']
        val_pos4_prev = parser[section_name]['slow_position_4']
    except Exception as e:
        print("exception loading slowmode setting: " + str(e))
        pass

    pos1_textbox.insert(END, val_pos1_prev)
    pos2_textbox.insert(END, val_pos2_prev)
    pos3_textbox.insert(END, val_pos3_prev)
    pos4_textbox.insert(END, val_pos4_prev)

    pos1_label.pack()
    pos1_textbox.pack()
    pos2_label.pack()
    pos2_textbox.pack()
    pos3_label.pack()
    pos3_textbox.pack()
    pos4_label.pack()
    pos4_textbox.pack()
    confirm_button.pack()

    slowmode_window.focus_set()
    window_count += 1

def toggle_switch_settings():
    global window_count

    section_name = "Toggle_switch"

    def quit_win():
        global window_count
        tss_window.destroy()
        window_count -= 1
    def ok():
        global needs_update
        eep_addr_filp_up_start = 80
        eep_addr_filp_down_start = 90

        if not parser.has_section(section_name):
            parser.add_section(section_name)

        selected = r_var.get()
        toggle_up_hotkey0 = drop_var_up0.get()
        toggle_up_hotkey1 = drop_var_up1.get()
        toggle_up_hotkey2 = drop_var_up2.get()
        toggle_up_hotkey3 = drop_var_up3.get()
        toggle_down_hotkey0 = drop_var_down0.get()
        toggle_down_hotkey1 = drop_var_down1.get()
        toggle_down_hotkey2 = drop_var_down2.get()
        toggle_down_hotkey3 = drop_var_down3.get()
        chat_command_up = flip_up_textbox.get()
        chat_command_down = flip_down_textbox.get()
        ts_nickname = ts_nickname_textbox.get()
        send_command_on_startup = var2.get()

        parser.set(section_name, "radiobutton_position", str(selected))
        parser.set(section_name, "toggle_up_hotkey0", str(toggle_up_hotkey0))
        parser.set(section_name, "toggle_up_hotkey1", str(toggle_up_hotkey1))
        parser.set(section_name, "toggle_up_hotkey2", str(toggle_up_hotkey2))
        parser.set(section_name, "toggle_up_hotkey3", str(toggle_up_hotkey3))
        parser.set(section_name, "toggle_down_hotkey0", str(toggle_down_hotkey0))
        parser.set(section_name, "toggle_down_hotkey1", str(toggle_down_hotkey1))
        parser.set(section_name, "toggle_down_hotkey2", str(toggle_down_hotkey2))
        parser.set(section_name, "toggle_down_hotkey3", str(toggle_down_hotkey3))
        parser.set(section_name, "chat_command_up", str(chat_command_up))
        parser.set(section_name, "chat_command_down", str(chat_command_down))
        parser.set(section_name, "ts_nickname", str(ts_nickname))
        parser.set(section_name, "send_command_on_startup", str(send_command_on_startup))

        if selected == 0 or selected == 2:
            eepwrite(ser, eep_addr_filp_up_start+9, 0)
            eepwrite(ser, eep_addr_filp_down_start+9, 0)
        else:
            for i in range(20):
                eepzero(ser, eep_addr_filp_up_start+i)

            eepwrite(ser, eep_addr_filp_up_start, key_dict[toggle_up_hotkey0])
            eepwrite(ser, eep_addr_filp_up_start+1, key_dict[toggle_up_hotkey1])
            eepwrite(ser, eep_addr_filp_up_start+2, key_dict[toggle_up_hotkey2])
            eepwrite(ser, eep_addr_filp_up_start+3, key_dict[toggle_up_hotkey3])

            eepwrite(ser, eep_addr_filp_down_start, key_dict[toggle_down_hotkey0])
            eepwrite(ser, eep_addr_filp_down_start+1, key_dict[toggle_down_hotkey1])
            eepwrite(ser, eep_addr_filp_down_start+2, key_dict[toggle_down_hotkey2])
            eepwrite(ser, eep_addr_filp_down_start+3, key_dict[toggle_down_hotkey3])

            eepwrite(ser, eep_addr_filp_up_start+9, 1)
            eepwrite(ser, eep_addr_filp_down_start+9, 1)

        dump_config(parser, config_filename)
        needs_update = 1
        check_toggle_switch_config(panel.toggle_sw1_position)
        quit_win()

    if window_count >= 1:
        print("too many windows")
        return
    tss_window = Toplevel(root)
    tss_window.title('Toggle Switch Settings')
    tss_window.geometry('700x300')
    tss_window.resizable(width=FALSE, height=FALSE)
    tss_window.protocol("WM_DELETE_WINDOW", quit_win)

    radiobutton_position_prev = 0
    toggle_up_hotkey0_prev = 'none'
    toggle_up_hotkey1_prev = 'none'
    toggle_up_hotkey2_prev = 'none'
    toggle_up_hotkey3_prev = 'none'
    toggle_down_hotkey0_prev = 'none'
    toggle_down_hotkey1_prev = 'none'
    toggle_down_hotkey2_prev = 'none'
    toggle_down_hotkey3_prev = 'none'
    chat_command_up_prev = ''
    chat_command_down_prev = ''
    ts_nickname_prev = ''
    send_command_on_startup_prev = 0
    try:
        radiobutton_position_prev = int(parser[section_name]['radiobutton_position'])
        toggle_up_hotkey0_prev = parser[section_name]['toggle_up_hotkey0']
        toggle_up_hotkey1_prev = parser[section_name]['toggle_up_hotkey1']
        toggle_up_hotkey2_prev = parser[section_name]['toggle_up_hotkey2']
        toggle_up_hotkey3_prev = parser[section_name]['toggle_up_hotkey3']
        toggle_down_hotkey0_prev = parser[section_name]['toggle_down_hotkey0']
        toggle_down_hotkey1_prev = parser[section_name]['toggle_down_hotkey1']
        toggle_down_hotkey2_prev = parser[section_name]['toggle_down_hotkey2']
        toggle_down_hotkey3_prev = parser[section_name]['toggle_down_hotkey3']
        chat_command_up_prev = parser[section_name]['chat_command_up']
        chat_command_down_prev = parser[section_name]['chat_command_down']
        ts_nickname_prev = parser[section_name]['ts_nickname']
        send_command_on_startup_prev = int(parser[section_name]['send_command_on_startup'])
    except Exception as e:
        print("exception loading toggle switch setting: " + str(e))

    r_var = IntVar()
    R0 = Radiobutton(tss_window, text="Not used", variable=r_var, value=0)
    R1 = Radiobutton(tss_window, text="Use this toggle switch as keyboard hotkey", variable=r_var, value=1)
    R2 = Radiobutton(tss_window, text="Use this toggle switch for chat command", variable=r_var, value=2)
    r_var.set(radiobutton_position_prev)
    R0.place(x=10, y=15)
    R1.place(x=10, y=40+10)
    R2.place(x=10, y=40+100)

    var2 = IntVar()
    startup_checkbox = Checkbutton(tss_window, text="Send commands on startup", variable=var2)
    startup_checkbox.place(x=350, y=255)
    var2.set(send_command_on_startup_prev)

    flip_up_label0 = Label(tss_window, text="flip up:")
    flip_up_label0.place(x=40, y=40+35)
    flip_up_label1 = Label(tss_window, text="flip up:")
    flip_up_label1.place(x=40, y=40+125)

    flip_down_label0 = Label(tss_window, text="flip down:")
    flip_down_label0.place(x=40, y=40+66)
    flip_down_label1 = Label(tss_window, text="flip down:")
    flip_down_label1.place(x=40, y=40+156)

    flip_up_textbox = Entry(tss_window)
    flip_up_textbox.insert(END, chat_command_up_prev)
    flip_up_textbox.place(x=110, y=40+123)
    flip_up_textbox.configure(width=30)

    flip_down_textbox = Entry(tss_window)
    flip_down_textbox.insert(END, chat_command_down_prev)
    flip_down_textbox.place(x=110, y=40+155)
    flip_down_textbox.configure(width=30)

    OPTIONS = [x[0] for x in key_list]
    drop_var_up0 = StringVar(tss_window)
    drop_var_up0.set(OPTIONS[OPTIONS.index(toggle_up_hotkey0_prev)])
    hotkey_dropdown0 = OptionMenu(tss_window, drop_var_up0, *OPTIONS)
    hotkey_dropdown0.config(width=15)
    hotkey_dropdown0.place(x=110, y=40+34)

    drop_var_up1 = StringVar(tss_window)
    drop_var_up1.set(OPTIONS[OPTIONS.index(toggle_up_hotkey1_prev)])
    hotkey_dropdown1 = OptionMenu(tss_window, drop_var_up1, *OPTIONS)
    hotkey_dropdown1.config(width=15)
    hotkey_dropdown1.place(x=255, y=40+34)

    drop_var_up2 = StringVar(tss_window)
    drop_var_up2.set(OPTIONS[OPTIONS.index(toggle_up_hotkey2_prev)])
    hotkey_dropdown2 = OptionMenu(tss_window, drop_var_up2, *OPTIONS)
    hotkey_dropdown2.config(width=15)
    hotkey_dropdown2.place(x=400, y=40+34)

    drop_var_up3 = StringVar(tss_window)
    drop_var_up3.set(OPTIONS[OPTIONS.index(toggle_up_hotkey3_prev)])
    hotkey_dropdown3 = OptionMenu(tss_window, drop_var_up3, *OPTIONS)
    hotkey_dropdown3.config(width=15)
    hotkey_dropdown3.place(x=545, y=40+34)

    # 
    drop_var_down0 = StringVar(tss_window)
    drop_var_down0.set(OPTIONS[OPTIONS.index(toggle_down_hotkey0_prev)])
    hotkey_dropdown0 = OptionMenu(tss_window, drop_var_down0, *OPTIONS)
    hotkey_dropdown0.config(width=15)
    hotkey_dropdown0.place(x=110, y=40+65)

    drop_var_down1 = StringVar(tss_window)
    drop_var_down1.set(OPTIONS[OPTIONS.index(toggle_down_hotkey1_prev)])
    hotkey_dropdown1 = OptionMenu(tss_window, drop_var_down1, *OPTIONS)
    hotkey_dropdown1.config(width=15)
    hotkey_dropdown1.place(x=255, y=40+65)

    drop_var_down2 = StringVar(tss_window)
    drop_var_down2.set(OPTIONS[OPTIONS.index(toggle_down_hotkey2_prev)])
    hotkey_dropdown2 = OptionMenu(tss_window, drop_var_down2, *OPTIONS)
    hotkey_dropdown2.config(width=15)
    hotkey_dropdown2.place(x=400, y=40+65)

    drop_var_down3 = StringVar(tss_window)
    drop_var_down3.set(OPTIONS[OPTIONS.index(toggle_down_hotkey3_prev)])
    hotkey_dropdown3 = OptionMenu(tss_window, drop_var_down3, *OPTIONS)
    hotkey_dropdown3.config(width=15)
    hotkey_dropdown3.place(x=545, y=40+65)

    plus = Label(tss_window, text="+")
    plus.place(x=244, y=40+36)
    plus1 = Label(tss_window, text="+")
    plus1.place(x=389, y=40+36)
    plus2 = Label(tss_window, text="+")
    plus2.place(x=534, y=40+36)
    plus3 = Label(tss_window, text="+")
    plus3.place(x=244, y=40+67)
    plus4 = Label(tss_window, text="+")
    plus4.place(x=389, y=40+67)
    plus5 = Label(tss_window, text="+")
    plus5.place(x=534, y=40+67)

    confirm_button = Button(tss_window, text ="Confirm", command = ok)
    confirm_button.place(x=610, y=40+215)

    ask_nickname = Label(tss_window, text="Toggle Switch Name: ")
    ask_nickname.place(x=15, y=40+190)
    ts_nickname_textbox = Entry(tss_window)
    ts_nickname_textbox.place(x=15, y=40+215)
    ts_nickname_textbox.configure(width=20)
    ts_nickname_textbox.insert(END, ts_nickname_prev)

    tss_window.focus_set()
    window_count += 1

def button_nickname_update(button_1_nickname_label, button_2_nickname_label, button_3_nickname_label, button_4_nickname_label, button_5_nickname_label, ts_nickname_label):
    button_1_nickname = ''
    button_2_nickname = ''
    button_3_nickname = ''
    button_4_nickname = ''
    button_5_nickname = ''
    ts_nickname = ''
    try:
        button_1_nickname = parser["Pushbutton 1"]['button_nickname']
    except Exception:
        pass
    try:
        button_2_nickname = parser["Pushbutton 2"]['button_nickname']
    except Exception:
        pass
    try:
        button_3_nickname = parser["Pushbutton 3"]['button_nickname']
    except Exception:
        pass
    try:
        button_4_nickname = parser["Pushbutton 4"]['button_nickname']
    except Exception:
        pass
    try:
        button_5_nickname = parser["Pushbutton 5"]['button_nickname']
    except Exception:
        pass
    try:
        ts_nickname = parser["Toggle_switch"]['ts_nickname']
    except Exception:
        pass
    button_1_nickname_label.configure(text=button_1_nickname)
    button_2_nickname_label.configure(text=button_2_nickname)
    button_3_nickname_label.configure(text=button_3_nickname)
    button_4_nickname_label.configure(text=button_4_nickname)
    button_5_nickname_label.configure(text=button_5_nickname)
    ts_nickname_label.configure(text=ts_nickname)

def check_button_config(state, index):
    if state != 1:
        return False
    section_name = "Pushbutton " + str(index)
    try:
        radiobutton_position = int(parser[section_name]["radiobutton_position"])
        chat_command = parser[section_name]["chat_command"]
        if radiobutton_position == 2:
            print("button " + str(index) + " message: " + chat_command)
            chat_bot.send_message(chat_command)
            draw_text(main_canvas, 505, 482, time.strftime("%H:%M:%S ") + chat_command, "last_action_time", color='red')
            return True
        return False
    except Exception as e:
        print("check_button_config: " + str(e))
        return False

def check_toggle_switch_config(state):
    if state != 0 and state != 1:
        return False
    section_name = "Toggle_switch"
    try:
        radiobutton_position = int(parser[section_name]["radiobutton_position"])
        chat_command_up = parser[section_name]["chat_command_up"]
        chat_command_down = parser[section_name]["chat_command_down"]
        if radiobutton_position == 2:
            if state == 1:
                print("toggle switch 1 up message: " + chat_command_up)
                chat_bot.send_message(chat_command_up)
                draw_text(main_canvas, 505, 482, time.strftime("%H:%M:%S ") + chat_command_up, "last_action_time", color='red')
                return True
            if state == 0:
                print("toggle switch 1 down message: " + chat_command_down)
                chat_bot.send_message(chat_command_down)
                draw_text(main_canvas, 505, 482, time.strftime("%H:%M:%S ") + chat_command_down, "last_action_time", color='red')
                return True
        return False
    except Exception as e:
        print("check_toggle_switch_config: " + str(e))
        return False

def rotary_switch_config(position):
    global rotary_sw0_dispatch
    if position == None:
        return False
    section_name = "Slowmode"
    slow1 = 3
    slow2 = 5
    slow3 = 10
    slow4 = 30
    try:
        slow1 = int(parser[section_name]["slow_position_1"])
        slow2 = int(parser[section_name]["slow_position_2"])
        slow3 = int(parser[section_name]["slow_position_3"])
        slow4 = int(parser[section_name]["slow_position_4"])
    except Exception as e:
        print("rotary_switch_config: " + str(e))
    slow_cmd_list = ['/slowoff', '/slow '+str(slow1), '/slow '+str(slow2), '/slow '+str(slow3), '/slow '+str(slow4)]
    rotary_sw0_dispatch = (slow_cmd_list[position], time.time() + 0.5)

def force_update():
    global panel
    while 1:
        time.sleep(0.1)
        gui_update_non_block()
        ser.write(('report\r\n').encode())
        serial_recv = serial_wait_for_response(ser)
        if serial_recv.startswith('report:'):
            message = serial_recv.lstrip("report:").rstrip(",end").split(",")
            for item in message:
                panel.parse(item)
            send_chat('ts0=' + str(panel.toggle_sw0_position))
            rotary_switch_config(panel.rotary_sw0_position)
            send_ts_channel_command = None
            try:
                send_command_on_startup_prev = int(parser['Toggle_switch']['send_command_on_startup'])
                pos = int(parser['Toggle_switch']['radiobutton_position'])
                if pos == 2 and send_command_on_startup_prev == 1:
                    send_ts_channel_command = 1
            except Exception as e:
                print("exception loading send_ts_channel_command in force_update: " + str(e))
            if send_ts_channel_command == 1:
                check_toggle_switch_config(panel.toggle_sw1_position)
            return

def send_chat(message):
    button0_status = None
    button1_status = None
    button2_status = None
    button3_status = None
    button4_status = None
    button5_status = None
    rotary_sw0_position = None
    toggle_sw0_position = None
    toggle_sw1_position = None

    if message.startswith("rs0"):
        rotary_sw0_position = int(message.split('=')[-1])
    elif message.startswith("ts0"):
        toggle_sw0_position = int(message.split('=')[-1])
    elif message.startswith("ts1"):
        toggle_sw1_position = int(message.split('=')[-1])
    elif message.startswith("pb0"):
        button0_status = int(message.split('=')[-1])
    elif message.startswith("pb1"):
        button1_status = int(message.split('=')[-1])
    elif message.startswith("pb2"):
        button2_status = int(message.split('=')[-1])
    elif message.startswith("pb3"):
        button3_status = int(message.split('=')[-1])
    elif message.startswith("pb4"):
        button4_status = int(message.split('=')[-1])
    elif message.startswith("pb5"):
        button5_status = int(message.split('=')[-1])

    if button0_status == 1:
        ad_time_list = [30, 60, 90, 120, 150]
        ad_length = str(ad_time_list[panel.rotary_sw1_position])
        cmd = "/commercial " + ad_length
        print("button 0 message: " + cmd)
        chat_bot.send_message(cmd)
        draw_text(main_canvas, 505, 482, time.strftime("%H:%M:%S ") + cmd, "last_action_time", color='red')
    if toggle_sw0_position == 1:
        cmd = "/subscribers"
        print("toggle switch 0 up message: " + cmd)
        chat_bot.send_message(cmd)
        draw_text(main_canvas, 505, 482, time.strftime("%H:%M:%S ") + cmd, "last_action_time", color='red')
    if toggle_sw0_position == 0:
        cmd = "/subscribersoff"
        print("toggle switch 0 down message: " + cmd)
        chat_bot.send_message(cmd)
        draw_text(main_canvas, 505, 482, time.strftime("%H:%M:%S ") + cmd, "last_action_time", color='red')

    check_button_config(button1_status, 1)
    check_button_config(button2_status, 2)
    check_button_config(button3_status, 3)
    check_button_config(button4_status, 4)
    check_button_config(button5_status, 5)
    check_toggle_switch_config(toggle_sw1_position)
    rotary_switch_config(rotary_sw0_position)

def draw_text(master, x, y, text, tag, color = 'black'):
    master.delete(tag)
    master.create_text(x, y, text=text, tag=tag, anchor=CENTER, fill=color)
    gui_update_non_block()

def main_window():
    global panel, needs_update, main_canvas, rotary_sw0_dispatch
    main_canvas.place(x=0, y=0)
    main_canvas.create_image(8, 10, image=panel_bg, anchor='nw')
    chat_display_queue = []
    chat_display_label = Label(root, text="", height = 5, width=30, anchor='nw', justify='left')
    chat_display_label.place(x=0, y=410)
    current_user_label = Label(root, text="Username: " + owner_username)
    current_user_label.place(x=247, y = 410)
    current_channel_label = Label(root, text="Channel: " + chat_channel)
    current_channel_label.place(x=247, y = 430)
    connection_setting_button = Button(root, text ="Connection Settings", command=lambda:try_login())
    connection_setting_button.place(x=322, y=462, anchor=CENTER)
    backlight_setting_button = Button(root, text ="Backlight Brightness", command=bl_settings)
    backlight_setting_button.place(x=322, y=487, anchor=CENTER)
    slowmode_setting_button = Button(root, text ="Slowmode Settings", command=slowmode_settings)
    slowmode_setting_button.place(x=302, y=203, anchor=CENTER)
    toggle_sw_setting_button = Button(root, text ="Toggle Switch Settings", command=toggle_switch_settings)
    toggle_sw_setting_button.place(x=505, y=127, anchor=CENTER)
    button_custom_button1 = Button(root, text = "1", command=lambda:button_custom(index = 1))
    button_custom_button1.place(x=545, y=173)
    button_custom_button2 = Button(root, text = "2", command=lambda:button_custom(index = 2))
    button_custom_button2.place(x=430, y=257)
    button_custom_button3 = Button(root, text = "3", command=lambda:button_custom(index = 3))
    button_custom_button3.place(x=545, y=257)
    button_custom_button4 = Button(root, text = "4", command=lambda:button_custom(index = 4))
    button_custom_button4.place(x=430, y=347)
    button_custom_button5 = Button(root, text = "5", command=lambda:button_custom(index = 5))
    button_custom_button5.place(x=545, y=347)
    button_1_nickname_label = Label(root, text='')
    button_2_nickname_label = Label(root, text='')
    button_3_nickname_label = Label(root, text='')
    button_4_nickname_label = Label(root, text='')
    button_5_nickname_label = Label(root, text='')
    ts_nickname_label = Label(root, text='')
    button_1_nickname_label.place(x=544, y=155)
    button_2_nickname_label.place(x=423, y=239)
    button_3_nickname_label.place(x=544, y=239)
    button_4_nickname_label.place(x=423, y=328)
    button_5_nickname_label.place(x=544, y=328)
    ts_nickname_label.place(x=531, y=65)

    button_nickname_update(button_1_nickname_label, button_2_nickname_label, button_3_nickname_label, button_4_nickname_label, button_5_nickname_label, ts_nickname_label)
    force_update()
    draw_panel(main_canvas)
    draw_text(main_canvas, 505, 460, "last chat command sent: ", "last_sent")

    while 1:
        if needs_update:
            button_nickname_update(button_1_nickname_label, button_2_nickname_label, button_3_nickname_label, button_4_nickname_label, button_5_nickname_label, ts_nickname_label)
            needs_update = 0
        time.sleep(0.01)
        gui_update_non_block()
        serial_recv = get_serial_message(ser)
        if serial_recv != '':
            print(serial_recv)
            panel.parse(serial_recv)
            draw_panel(main_canvas)
            send_chat(serial_recv)

        if rotary_sw0_dispatch != None and time.time() > rotary_sw0_dispatch[1]:
            cmd = rotary_sw0_dispatch[0]
            print("slowmode message: " + cmd)
            chat_bot.send_message(cmd)
            draw_text(main_canvas, 505, 482, time.strftime("%H:%M:%S ") + cmd, "last_action_time", color='red')
            rotary_sw0_dispatch = None

        chat_display_queue += chat_bot.get_parsed_message()
        while len(chat_display_queue) > 5:
            chat_display_queue.pop(0)
        chat_display_str = ''
        for item in chat_display_queue:
            if item.message_type == "PRIVMSG":
                chat_display_str += item.username + ": " + item.message + "\n"
            elif item.message_type == "NOTICE":
                chat_display_str += item.message + '\n'
        try:
            if len(chat_display_str) >= 2:
                chat_display_label.configure(text = chat_display_str)
        except Exception as e:
            print("fucking windows can't print twitch chat: " + str(e))
        current_user_label.configure(text="Username: " + owner_username)
        current_channel_label.configure(text="Channel: " + chat_channel)

device_port = serial_init()
ser = serial.Serial(device_port, 57600, timeout=0)
try_login(auto=True)
main_window()

