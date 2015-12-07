import os
import sys
import glob
import json
import time
import serial
from urllib.request import urlopen
from urllib.error import HTTPError

def find_device():
    if sys.platform.startswith('win'):
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        ports = [s[0] for s in ports]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')[::-1]
    else:
        raise EnvironmentError('Unsupported platform')
    import serial
    magic_word = "theresbeentonsoffuckupseverywhere"
    for port in ports:
        try:
            s = serial.Serial(port, 57600, timeout=0.5)
            s.write(('thiswholerunisajoke\r\n').encode())
            s.write(('thiswholerunisajoke\r\n').encode())
            if magic_word in s.read(len(magic_word)).decode():
                s.close()
                return str(port)
            s.close()
        except (OSError, serial.SerialException) as e:
            print(e)
            pass
    return ''

def local_file(name):
    return os.path.join(os.path.curdir, name)

def channel_type_check(channel): 
    def is_group_chat(name):
        return len(name) > 0 and name[0] == "_" and name.count("_") >= 2 and name[-13:].isnumeric()
    if len(channel) <= 0 or len(channel) > 50:
        return []
    url = "http://api.twitch.tv/api/channels/" + channel + "/chat_properties"
    while 1:
        try:
            info = json.loads(urlopen(url, timeout = 5).read().decode('utf-8'))
            return info["chat_servers"]
        except Exception as e:
            print("channel_type_check: " + str(e))
            code = -1
            try:
                code = e.code
            except:
                print("not http error")
            if code == 404:
                if is_group_chat(channel):
                    return ["192.16.64.180:443", "192.16.64.212:443", "192.16.64.180:6667", "192.16.64.212:6667"]
                else:
                    return []

def get_serial_message(ser):
    result = ser.read().decode()
    if len(result) <= 0:
        return ''
    entry_time = time.time()
    message = "" + result
    while 1:
        message += ser.read().decode()
        if '\n' in message:
            return message.split('\n')[0].replace('\r', '')
        if time.time() - entry_time > 1:
            return ''

def serial_wait_for_response(ser, timeout = 0.3):
    entry_time = time.time()
    message = ''
    while 1:
        message += ser.read().decode()
        if '\n' in message:
            return message.split('\n')[0].replace('\r', '')
        if time.time() - entry_time > 1:
            print("serial_wait_for_response timed out")
            return ''

def eepwrite(ser, addr, value):
    while 1:
        print('writing ' + str(value) + " to addr " + str(addr))
        ser.write(('eepwrite ' + str(addr) + " " + str(value) + "\r\n").encode())
        response = serial_wait_for_response(ser)
        if response.startswith("ew:"):
            response = response.lstrip("ew:").split("=")
            if len(response) >= 2 and int(response[0]) == addr and int(response[1]) == value:
                return
        time.sleep(0.1)

def eepread(ser, addr):
    while 1:
        print('reading eeprom addr ' + str(addr))
        ser.write(('eepread ' + str(addr) + "\r\n").encode())
        response = serial_wait_for_response(ser)
        if response.startswith("er:"):
            response = response.lstrip("er:").split("=")
            if len(response) >= 2 and int(response[0]) == addr:
                return int(response[1])
        time.sleep(0.1)

def setbacklight(ser, intensity):
    while 1:
        ser.write(('setbacklight ' + str(intensity) + "\r\n").encode())
        response = serial_wait_for_response(ser)
        if response.startswith("sb:"):
            response = response.lstrip("sb:")
            if int(response) == intensity:
                return
        time.sleep(0.1)

def eeprom_read_str(ser, addr_start, length):
    result = ''
    for i in range(addr_start, addr_start + length):
        result += chr(eepread(ser, i))
    return result

def eeprom_write_str(ser, message, addr_start, length):
    current_addr = addr_start
    message = fill_str(message, length)
    for c in message[:length]:
        eepwrite(ser, current_addr, ord(c))
        current_addr += 1

def eepzero(ser, addr):
    while 1:
        print('zeroing eeprom addr ' + str(addr))
        ser.write(('eepzero ' + str(addr) + "\r\n").encode())
        response = serial_wait_for_response(ser)
        if response.startswith("ez:"):
            response = response.lstrip("ez:").split("=")
            if len(response) >= 2 and int(response[1]) == 0:
                return
        time.sleep(0.1)

def fill_str(msg, length):
    msg = msg[:length]
    while len(msg) < length:
        msg = msg + chr(0)
    return msg

def is_int(string):
    try:
        value = int(string)
        if value > 0:
            return True
        return False
    except Exception:
        return False

class panel_status():
    def __init__(self):
        self.rotary_sw0_position = 0
        self.rotary_sw1_position = 0
        self.toggle_sw0_position = 0
        self.toggle_sw1_position = 0
        self.button0_status = 0
        self.button1_status = 0
        self.button2_status = 0
        self.button3_status = 0
        self.button4_status = 0
        self.button5_status = 0

    def parse(self, message):
        if message.startswith("rs0"):
            self.rotary_sw0_position = int(message.split('=')[-1])
        elif message.startswith("rs1"):
            self.rotary_sw1_position = int(message.split('=')[-1])
        elif message.startswith("ts0"):
            self.toggle_sw0_position = int(message.split('=')[-1])
        elif message.startswith("ts1"):
            self.toggle_sw1_position = int(message.split('=')[-1])
        elif message.startswith("pb0"):
            self.button0_status = int(message.split('=')[-1])
        elif message.startswith("pb1"):
            self.button1_status = int(message.split('=')[-1])
        elif message.startswith("pb2"):
            self.button2_status = int(message.split('=')[-1])
        elif message.startswith("pb3"):
            self.button3_status = int(message.split('=')[-1])
        elif message.startswith("pb4"):
            self.button4_status = int(message.split('=')[-1])
        elif message.startswith("pb5"):
            self.button5_status = int(message.split('=')[-1])

