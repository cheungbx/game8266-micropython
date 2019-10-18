# ESP8266 iot humdity temperature sensor with LED switch and pump switch , MQTT and  NTP time.
# press LEFT button to exit the program.
# ----------------------------------------------------------

# ESP8266 (node MCU D1 mini)  micropython
# by Billy Cheung  2019 08 31
#
# SPI OLED
# GND
# VCC
# D0/Sck - D5 (=GPIO14=HSCLK)
# D1/MOSI- D7 (=GPIO13=HMOSI)
# RES    - D0 (=GPIO16)
# DC     - D4 (=GPIO2)
# CS     - D3 (=GPIO0)
# 
# GPIO15   D8  LED  / Speaker
# n.c.   - D6  (=GPIO13=HMOSI)
#
# GPIO5    D1——   On to read ADC for Btn / SCL for i2c sensors
# GPIO4    D2——   On to read ADC for Paddle / SDA for i2c sensors
#
# buttons   A0
# A0 VCC-9K-U-9K-L-12K-R-9K-D-9K-A-12K-B-9K-GND
import gc
import sys
gc.collect()
print (gc.mem_free())
import network

import time
from time import sleep_ms,ticks_ms, ticks_us, ticks_diff
from machine import Pin, SPI, PWM, ADC, I2C, RTC
from math import sqrt
import ssd1306
from random import getrandbits, seed

# configure oled display SPI SSD1306
hspi = SPI(1, baudrate=8000000, polarity=0, phase=0)
#DC, RES, CS
display = ssd1306.SSD1306_SPI(128, 64, hspi, Pin(2), Pin(16), Pin(0))



#---buttons

btnU = const (1 << 1)
btnL = const (1 << 2)
btnR = const (1 << 3)
btnD = const (1 << 4)
btnA = const (1 << 5)
btnB = const (1 << 6)

Btns = 0
lastBtns = 0

pinBtn = Pin(5, Pin.OUT)
pinPaddle = Pin(4, Pin.OUT)


buzzer = Pin(15, Pin.OUT)

adc = ADC(0)

def getPaddle () :
  pinPaddle.on()
  pinBtn.off()
  sleep_ms(20)
  return adc.read()

def pressed (btn, waitRelease=False) :
  global Btns
  if waitRelease and Btns :
    pinPaddle.off()
    pinBtn.on()
    while ADC(0).read() > 70 :
       sleep_ms (20)
  return (Btns & btn)

def lastpressed (btn) :
  global lastBtns
  return (lastBtns & btn)


def getBtn () :
  global Btns
  global lastBtns
  pinPaddle.off()
  pinBtn.on()
  lastBtns = Btns
  Btns = 0
  a0=ADC(0).read()
  if a0  < 564 :
    if a0 < 361 :
      if a0 > 192 :
        if a0 > 278 :
          Btns |= btnU | btnA
        else :
          Btns |= btnL
      else:
        if a0 > 70 :
          Btns |= btnU
    else :
      if a0 > 482 :
        if a0 > 527 :
          Btns |= btnD
        else :
          Btns |= btnU | btnB
      else:
        if a0 > 440 :
          Btns |= btnL | btnA
        else :
          Btns |= btnR
  else:
      if a0 < 728 :
        if a0 < 653 :
          if a0 > 609 :
            Btns |= btnD | btnA
          else :
            Btns |= btnR | btnA
        elif a0 > 675 :
          Btns |= btnA
        else :
          Btns |= btnL | btnB
      elif a0 < 829 :
        if a0 > 794 :
          Btns |= btnD | btnB
        else :
          Btns |= btnR | btnB
      elif a0 > 857 :
        Btns |= btnB
      else :
        Btns |= btnA | btnB


# ----------------------------------------------------------
# Global variables
# ----------------------------------------------------------




from struct import unpack as unp
led = Pin(15, Pin.OUT) 




# turn off everything
led.off()

  

 

reported_err = 0
measure_period_ms = const(5000)
display_period_ms = const(1000)
last_measure_ms = 0
last_display_ms = 0

ledOn = False
pumpOn = False
h = 0
h0 = 1.0
t = 0
t0 = 1.0
lux = 0
lux0 = 10



# SHT20 default address
SHT20_I2CADDR = const (64)

# SHT20 Command
TRI_T_MEASURE_NO_HOLD = b'\xf3'
TRI_RH_MEASURE_NO_HOLD = b'\xf5'
READ_USER_REG = b'\xe7'
WRITE_USER_REG = b'\xe6'
SOFT_RESET = b'\xfe'


def sht20_temperature(i2c):
  try:
    i2c.writeto(SHT20_I2CADDR, TRI_T_MEASURE_NO_HOLD)
    sleep_ms(150)
    origin_data = i2c.readfrom(SHT20_I2CADDR, 2)
    origin_value = unp('>h', origin_data)[0]
    value = -46.85 + 175.72 * (origin_value / 65536)
  except OSError as err :
    print("sht20 temperature error: {0}".format(err))
    return 0
  return value

def sht20_relative_humidity(i2c):
  try:
    i2c.writeto(SHT20_I2CADDR, TRI_RH_MEASURE_NO_HOLD)
    sleep_ms(150)
    origin_data = i2c.readfrom(SHT20_I2CADDR, 2)
    origin_value = unp('>H', origin_data)[0]
    value = -6 + 125 * (origin_value / 65536)
  except OSError as err :
    print("sht20 humdity error: {0}".format(err))
    return 0
  return value  

# BH1750fvi light meter sensor 
OP_SINGLE_HRES1 = 0x20
OP_SINGLE_HRES2 = 0x21
OP_SINGLE_LRES = 0x23

DELAY_HMODE = 180  # 180ms in H-mode
DELAY_LMODE = 24  # 24ms in L-mode


def bh1750fvi (i2c, mode=OP_SINGLE_HRES1, i2c_addr=0x23):
  """
      Performs a single sampling. returns the result in lux
  """
  try:
    i2c.writeto(i2c_addr, b"\x00")  # make sure device is in a clean state
    i2c.writeto(i2c_addr, b"\x01")  # power up
    i2c.writeto(i2c_addr, bytes([mode]))  # set measurement mode

    sleep_ms(DELAY_LMODE if mode == OP_SINGLE_LRES else DELAY_HMODE)

    raw = i2c.readfrom(i2c_addr, 2)
    i2c.writeto(i2c_addr, b"\x00")  # power down again
  except OSError as err :
    print("bh1750fvi lux error: {0}".format(err))
    return 0
  # we must divide the end result by 1.2 to get the lux
  return ((raw[0] << 24) | (raw[1] << 16)) // 78642


def fill_zero(n):   
    if n < 10:   
        return '0' + str(n) 
    else:   
        return str(n) 

def fill_blank(n):     
    if n<10:
        return ' ' + str(n)
    else:
        return str(n)
 

        
# WiFi connection information
WIFI_SSID = 'BILLYWIFI'
WIFI_PASSWORD = 'Xolmem13'

# turn off the WiFi Access Point
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)

# connect the device to the WiFi network
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASSWORD)

# wait until the device is connected to the WiFi network
MAX_ATTEMPTS = 20
attempt_count = 0
while not wifi.isconnected() and attempt_count < MAX_ATTEMPTS:
    attempt_count += 1
    sleep_ms(1000)

if attempt_count == MAX_ATTEMPTS:
    print('could not connect to the WiFi network')
    sys.exit()

# set time using NTP server on the internet

import ntptime    #NTP-time (from pool.ntp.org) 
import utime
ntptime.settime()
tm = utime.localtime(utime.mktime(utime.localtime()) + 8 * 3600)
tm=tm[0:3] + (0,) + tm[3:6] + (0,)
rtc = RTC()
rtc.datetime(tm)

ContinueOn = True
while ContinueOn :

  
  getBtn()
  
  if pressed (btnL, True) :
    ContinueOn = False
  
  elif pressed(btnA,True) :                 
    #LED buttun pressed and released
    if ledOn :
      # if led is previously ON, now turn it off by outputing High voltage
      led.off()
      msg = "OFF"
      ledOn = False
    else :
      # if led is previously OFF, now turn it on by outputing Low voltage
      led.on()
      msg = "ON"
      ledOn = True



  if ticks_diff(ticks_ms(), last_measure_ms ) >=  measure_period_ms :

    # time to take measurements    
    # Pin 4 and 5 is multiplexed between I2C and Btn ADC control.
    # set up PIn 4 and 5 for I2C
    
    i2c = I2C(-1, Pin(5), Pin(4))   # SCL, SDA
    t = sht20_temperature(i2c)
    h = sht20_relative_humidity(i2c)
    lux = bh1750fvi(i2c) 
    
    # Pin 4 and 5 is multiplexed between I2C and Btn ADC control.
    # set up PIn 4 and 5 for Btn ADC control.
    pinBtn = Pin(5, Pin.OUT)  
    pinPaddle = Pin(4, Pin.OUT)
    
    if lux != lux0 :
        print('Publish:  lux = {}'.format(lux))
        lux0 = lux
        
    if h != h0 :
        print('Publish:  humidity = {}'.format(h))
        h0 = h

    msg = (b'{0:3.1f}'.format(t))
    if t != t0 :
        print('Publish:  airtemp = {}'.format(t))
        t0 = t
        
    last_measure_ms = ticks_ms()

  if ticks_diff(ticks_ms(), last_display_ms) >= display_period_ms :
    # time to display 
    display.fill(0)
    Y,M,D,H,m,S,ms,W=utime.localtime()
    timetext ='%s-%s %s:%s:%s' % (fill_zero(M),fill_zero(D),fill_zero(H),fill_zero(m),fill_zero(S))       
    display.text(timetext,0,0)
    display.text('Lux = {}'.format(lux), 0, 15)
    display.text(b'{0:3.1f} %'.format(h), 0, 30)
    display.text(b'{0:3.1f} C'.format(t), 64, 30)  
    if ledOn :
        display.text("LED ON", 0, 48)
    else :
        display.text("LED OFF", 0, 48)
                     

    display.show()  
    last_display_ms = ticks_ms()

i2c.stop()
pinBtn = Pin(5, Pin.OUT)  
pinPaddle = Pin(4, Pin.OUT)





