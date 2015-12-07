#include <stdint.h>
#include <EEPROM.h>
#include <Keyboard.h>
#include "serial_util.h"
#include "input_util.h"
#define RECV_BUF_SIZE 64
#define PUSH_BUTTON_COUNT 6
#define TOGGLE_SWITCH_COUNT 2
#define ROTARY_SWITCH_COUNT 2
#define LED_PIN 10
#define EEP_BACKLIGHT_VALUE_ADDR 10

const int16_t BUTTON_PIN_ARRAY[6] = {A2, A1, A0, 15, 14, 16};
const int16_t ROTARY_SW_PIN_ARRAY[2] = {A7, A6};
const int16_t TOGGLE_SW_PIN_ARRAY[2] = {9, 8};
char recv_buf[RECV_BUF_SIZE];
int16_t backlight_val = 0;
int32_t next_eep_backlight_write = -1;
my_button push_button_array[PUSH_BUTTON_COUNT];
my_toggle_switch toggle_switch_array[TOGGLE_SWITCH_COUNT];
my_rotary_switch rotary_switch_array[ROTARY_SWITCH_COUNT];

void setup()
{
	Serial.begin(57600);
	for (int i = 0; i < PUSH_BUTTON_COUNT; i++)
		pinMode(BUTTON_PIN_ARRAY[i], INPUT_PULLUP);
	for (int i = 0; i < ROTARY_SWITCH_COUNT; i++)
		pinMode(ROTARY_SW_PIN_ARRAY[i], INPUT);
	for (int i = 0; i < TOGGLE_SWITCH_COUNT; i++)
		pinMode(TOGGLE_SW_PIN_ARRAY[i], INPUT);
	pinMode(LED_PIN, OUTPUT);

	for (int i = 0; i < PUSH_BUTTON_COUNT; i++) 
		push_button_array[i].init(BUTTON_PIN_ARRAY[i], i);
	for (int i = 0; i < TOGGLE_SWITCH_COUNT; i++) 
		toggle_switch_array[i].init(TOGGLE_SW_PIN_ARRAY[i], i); 
	for (int i = 0; i < ROTARY_SWITCH_COUNT; i++) 
		rotary_switch_array[i].init(ROTARY_SW_PIN_ARRAY[i], i);
	Keyboard.begin();
	analogWrite(LED_PIN, EEPROM.read(EEP_BACKLIGHT_VALUE_ADDR));
}

void do_report()
{
	Serial.print("report:");
	for (int i = 0; i < PUSH_BUTTON_COUNT; i++) 
		push_button_array[i].report(); 
	for (int i = 0; i < TOGGLE_SWITCH_COUNT; i++) 
		toggle_switch_array[i].report();
	for (int i = 0; i < ROTARY_SWITCH_COUNT; i++) 
		rotary_switch_array[i].report();
	Serial.println("end");
}

void loop()
{
	delay(10);
	for (int i = 0; i < PUSH_BUTTON_COUNT; i++) 
		push_button_array[i].refresh(); 
	for (int i = 0; i < TOGGLE_SWITCH_COUNT; i++) 
		toggle_switch_array[i].refresh();
	for (int i = 0; i < ROTARY_SWITCH_COUNT; i++) 
		rotary_switch_array[i].refresh();

    if(next_eep_backlight_write != -1 && millis() > next_eep_backlight_write)
    {
        EEPROM.write(EEP_BACKLIGHT_VALUE_ADDR, backlight_val);
        next_eep_backlight_write = -1;
    }

	if(get_serial_command(recv_buf, RECV_BUF_SIZE) != -1)
	{
		if(strncmp(recv_buf, "thiswholerunisajoke\n", 20) == 0)
			Serial.println("theresbeentonsoffuckupseverywhere");
		if(strncmp(recv_buf, "report\n", 5) == 0)
			do_report();
		if(strncmp(recv_buf, "setbacklight ", 13) == 0)
        {
            int16_t arg1_pos = goto_next_arg(0, recv_buf, RECV_BUF_SIZE);
            backlight_val = atoi(recv_buf + arg1_pos);
            analogWrite(LED_PIN, backlight_val);
            next_eep_backlight_write = millis() + 1000;
            Serial.print("sb:");
            Serial.println(backlight_val, DEC);
        }
        if(strncmp(recv_buf, "eepread ", 8) == 0)
        {
            int16_t arg1_pos = goto_next_arg(0, recv_buf, RECV_BUF_SIZE);
            int16_t address = atoi(recv_buf + arg1_pos);
            Serial.print("er:");
            Serial.print(address, DEC);
            Serial.write('=');
            Serial.println(EEPROM.read(address));
        }
        if(strncmp(recv_buf, "eepwrite ", 9) == 0)
        {
            int16_t arg1_pos = goto_next_arg(0, recv_buf, RECV_BUF_SIZE);
            int16_t arg2_pos = goto_next_arg(arg1_pos, recv_buf, RECV_BUF_SIZE);
            int16_t address = atoi(recv_buf + arg1_pos);
            uint8_t value = (uint8_t)atoi(recv_buf + arg2_pos);
            EEPROM.write(address, value);
            Serial.print("ew:");
            Serial.print(address, DEC);
            Serial.write('=');
            Serial.println(EEPROM.read(address));
        }
        if(strncmp(recv_buf, "eepzero ", 8) == 0)
        {
            int16_t arg1_pos = goto_next_arg(0, recv_buf, RECV_BUF_SIZE);
            int16_t address = atoi(recv_buf + arg1_pos);
            if(EEPROM.read(address) != 0)
            	EEPROM.write(address, 0);
            Serial.print("ez:");
            Serial.print(address, DEC);
            Serial.write('=');
            Serial.println(EEPROM.read(address));
        }
        if(strncmp(recv_buf, "completeandutterchokerinintensesituations\n", 43) == 0)
        {
            for (int i = 0 ; i < EEPROM.length() ; i++)
            	if(EEPROM.read(i) != 0)
			    	EEPROM.write(i, 0);
            Serial.println("EEPROM erase complete");
        }
	}
}











