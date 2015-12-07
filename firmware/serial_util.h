#ifndef SERIAL_UTIL_H
#define SERIAL_UTIL_H
#include <Arduino.h>
#include <stdint.h>

int32_t enter_time;

int8_t get_serial_command(char buf[], int16_t size)
{
	enter_time = millis();
	if(Serial.available())
	{
		int16_t count = 0;
		memset(buf, 0, size);
		char c;
		while(1)
		{
			if(millis() - enter_time >= 250)
			{
				memset(buf, 0, size);
				return -1;
			}
			if(Serial.available())
			{
				c = Serial.read();
				if(c == '\r')
					continue;
				if(count < size - 1)
					buf[count] = c;
				count++;
				if(c == '\n')
					return 0;
			}
		}
	}
	else
		return -1;
}

int16_t goto_next_arg(int16_t current_pos, char* buf, int16_t size)
{
    while(current_pos < size && buf[current_pos] != ' ')
        current_pos++;
    while(current_pos < size && buf[current_pos] == ' ')
        current_pos++;
    return current_pos;
}

#endif

/*

EEPROM map
0 - 18 device information
20 - 28 key configuration for pushbutton 0
29 pushbutton 0 keyboard enable 
30 - 38 key configuration for pushbutton 1
40 48 pushbutton 2
50 58 pushbutton 3
60 68 pushbutton 4
70 78 pushbutton 5
80 109 username
110 139 channel
140 169 OAuth
*/