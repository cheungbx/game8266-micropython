# game8266-micropython
Micropython retro game system built using ESP8266 with either I2C or SPI SSD1306 OLED display, buttons , paddles and sound, game module game8266 makes writing games a lot easier.
# game8266.py 
# common micropython module for ESP8266 game board designed by Billy Cheung (c) 2019 08 31
# --usage--

# set the following line in game8266.py file at the __init__ function
#        self.useSPI = True  # for SPI display , with buttons read through ADC
#        self.useSPI = False  # for I2C display, and individual hard buttons
#
#  esp8266 is very bad at running .py source code files
# with its very limited CPU onboard memory of 32K 
# so to run any program with > 300 lines of codes combined (including all modules), you need to convert 
# source files into byte code first to avoid running out of memory.
# Type is command to convert game8266.py to the byte code file game8266.mpy  using mpy-cross.
#        mpy-cross game8266.py
# then copy the game8266.mpy file to the micropython's import directory on the flash
# create your game and leaverge the functions to display, read buttons and paddle and make sounds
# from the game8266 class module.
# Add this line to your micropython game source code (examples attached, e.g. invader.py)
#       from game8266 import Game8266, Rect
#       g=Game8266()
#
#
#-----------------------------------------
# SPI version of game board layout
# ----------------------------------------
# micropython game hat module to use SSD1306 SPI OLED, 6 buttons and a paddle
# SPI display runs 5 times faster than I2C  display in micropython and you need this speeds
# for games with many moving graphics (e.g. space invdader, breakout).
#
# Buttons are read through A0 using many resistors in a  Voltage Divider circuit
# ESP8266 (node MCU D1 mini)  micropython
#
# SPI OLED
# GND
# VCC
# D0/Sck - D5 (=GPIO14=HSCLK)
# D1/MOSI- D7 (=GPIO13=HMOSI)
# RES    - D0 (=GPIO16)
# DC     - D4 (=GPIO2)
# CS     - D3 (=GPIO0)
# Speaker
# GPIO15   D8  Speaker
# n.c.   - D6  (=GPIO12=HMISO)
#
# The ADC(0) (aka A0) is used to read both paddles and Buttons
# these two pins together control whether buttons or paddle will be read
# GPIO5    D1—— PinBtn
# GPIO4    D2—— pinPaddle
# To read buttons - Pin.Btn.On()  Pin.Paddle.off()
# To read paddle  - Pin.Btn.Off()  Pin.Paddle.on()
#
# buttons are connected in series to create a voltage dividor
# Each directional and A , B button when pressed will connect that point of
# the voltage dividor to A0 to read the ADC value to determine which button is pressed.
# resistor values are chosen to ensure we have at least a gap of 10 between each button combinations.
# L, R, U, D, can be pressed individually but not toghether.
# A, B, can be pressed invididually but not together.
# any one of A or B, can be pressed together with any one of L,R,U,D
# so you can move the gun using L,R, U,D, while shooting with A or B.
#
# refer to the schematics on my github for how to hook it up
#
# 3.3V-9K-Up-9K-Left-12K-Right-9K-Down-9K-A button-12K-B Button-9K-GND
#
#-----------------------------------------
# I2C version of game board layout
# ----------------------------------------
# mocropython game hat module to use SSD1306 I2C OLED, 6 buttons and a paddle
# I2C display runs 5 times slower than I2C display in micropython.
# Games with many moving graphics (e.g. space invdader, breakout) will run slower.
#
# Buttons are read through indvidial GPIO pins (pulled high).
#
# I2C OLED SSD1306
# GPIO4   D2---  SDA OLED
# GPIO5   D1---  SCL  OLED
#
# Speaker
# GPIO15  D8     Speaker
#
# Buttons are connect to GND when pressed, except for B button
# GPIO12  D6——   Left  
# GPIO13  D7——   Right     
# GPIO14  D5——   UP    
# GPIO2   D4——   Down    
# GPIO0   D3——   A
# GPIO16   D0——  B
# * GPIO16 cannot be pulled high by softeware, connect a 10K resisor to VCC to pull high
