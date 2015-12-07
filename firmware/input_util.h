#ifndef INPUT_UTIL_H
#define INPUT_UTIL_H

#include <Arduino.h>
#include <EEPROM.h>
#include <Keyboard.h>
#include <stdint.h>
#include <stdlib.h>

class my_button
{
private:
	int16_t pin, prev_state, button_index;
public:
	void init(int16_t pin_num, int16_t index)
	{
		pin = pin_num;
		prev_state = digitalRead(pin) == 1 ? 0 : 1;
		button_index = index;
	}

	void keyboard_event(int16_t current_state)
	{
		int16_t addr_start = (button_index + 2) * 10;
		int16_t addr_keyboard_enable = addr_start + 9;
		if(current_state == 1 && prev_state == 0 && EEPROM.read(addr_keyboard_enable))
		{
			for (int i = 0; i < 9; i++)
			{
				uint8_t value = EEPROM.read(addr_start + i);
				if(value != 0)
				{
					Keyboard.press(value);
					delay(50);
				}
			}
		}
		
		if(current_state == 0 && prev_state == 1 && EEPROM.read(addr_keyboard_enable))
		{
			for (int i = 0; i < 9; i++)
			{
				uint8_t value = EEPROM.read(addr_start + i);
				if(value != 0)
					Keyboard.release(value);
			} 
		}
	}

	void refresh()
	{
		int16_t current_state = digitalRead(pin) == 1 ? 0 : 1;
		if(current_state != prev_state)
		{
			keyboard_event(current_state);
			Serial.print("pb");
			Serial.print(button_index);
			Serial.write('=');
			Serial.print(current_state);
			Serial.println();
			delay(25);
		}
		prev_state = current_state;
	}

	int16_t report()
	{
		refresh();
		Serial.print("pb");
		Serial.print(button_index);
		Serial.write('=');
		Serial.print(prev_state);
		Serial.write(',');
	}
};

class my_toggle_switch
{
private:
	int16_t pin, prev_state, button_index;
public:
	void init(int16_t pin_num, int16_t index)
	{
		pin = pin_num;
		prev_state = analogRead(pin) > 100 ? 0 : 1;
		button_index = index;
	}

	void keyboard_event(int16_t current_state)
	{
		if(button_index != 1)
			return;
		int16_t flip_up_addr_start = 80;
		int16_t flip_up_keyboard_enable = flip_up_addr_start + 9;
		int16_t flip_down_addr_start = 90;
		int16_t flip_down_keyboard_enable = flip_down_addr_start + 9;
		// flipping up
		if(current_state == 1 && prev_state == 0 && EEPROM.read(flip_up_keyboard_enable))
		{
			for (int i = 0; i < 9; i++)
			{
				uint8_t value = EEPROM.read(flip_up_addr_start + i);
				if(value != 0)
				{
					Keyboard.press(value);
					delay(50);
				}
			}
			delay(200);
			for (int i = 0; i < 9; i++)
			{
				uint8_t value = EEPROM.read(flip_up_addr_start + i);
				if(value != 0)
					Keyboard.release(value);
			}
		}
		// flipping down
		if(current_state == 0 && prev_state == 1 && EEPROM.read(flip_down_keyboard_enable))
		{
			for (int i = 0; i < 9; i++)
			{
				uint8_t value = EEPROM.read(flip_down_addr_start + i);
				if(value != 0)
				{
					Keyboard.press(value);
					delay(50);
				}
			}
			delay(200);
			for (int i = 0; i < 9; i++)
			{
				uint8_t value = EEPROM.read(flip_down_addr_start + i);
				if(value != 0)
					Keyboard.release(value);
			} 
		}
	}

	void refresh()
	{
		int16_t current_state = analogRead(pin) > 100 ? 0 : 1;
		if(current_state != prev_state)
		{
			keyboard_event(current_state);
			Serial.print("ts");
			Serial.print(button_index);
			Serial.write('=');
			Serial.print(current_state);
			Serial.println();
			delay(25);
		}
		prev_state = current_state;
	}

	int16_t report()
	{
		refresh();
		Serial.print("ts");
		Serial.print(button_index);
		Serial.write('=');
		Serial.print(prev_state);
		Serial.write(',');
	}
};

class my_rotary_switch
{
private:
	int16_t pin, prev_position, button_index;
	int16_t read_rotary_switch_position()
	{
		int16_t analog_val_10b = analogRead(pin);
		if(analog_val_10b >= 595 && analog_val_10b <= 795)
			return 1;
		else if(analog_val_10b >= 412 && analog_val_10b <= 612)
			return 2;
		else if(analog_val_10b >= 79 && analog_val_10b <= 279)
			return 3;
		else if(analog_val_10b >= 0 && analog_val_10b <= 30)
			return 4;
		else
			return 0;
	}
public:
	void init(int16_t pin_num, int16_t index)
	{
		pin = pin_num;
		prev_position = read_rotary_switch_position();
		button_index = index;
	}

	void refresh()
	{
		int16_t current_position = read_rotary_switch_position();
		if(abs(current_position - prev_position) != 1)
			return;
		if(current_position == 1)
		{
			delay(100);
			current_position = read_rotary_switch_position();
		}
		if(current_position != prev_position)
		{
			Serial.print("rs");
			Serial.print(button_index);
			Serial.write('=');
			Serial.print(current_position);
			Serial.println();
			delay(100);
		}
		prev_position = current_position;
	}

	int16_t report()
	{
		refresh();
		Serial.print("rs");
		Serial.print(button_index);
		Serial.write('=');
		Serial.print(prev_position);
		Serial.write(',');
	}
};

#endif