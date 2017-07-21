#!/usr/bin/python

from printer import *


printer = Usb(0x04b8,0x0201)

if printer is not None:
       printer.reset()

