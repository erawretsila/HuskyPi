#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Example.py
#  
#  Copyright 2020  <pi@RoboTank>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
import HuskyPi as HL
from time import sleep

def main(args):
    hl=HL.HuskyLens(mode=HL.I2C)    ## creat HuskyLens instance
    hl.set_mode(HL.ALGORITHM_LINE_TRACK)    ##switch to Line follow mode
    while True:
        print (hl.execute(decode=True))   ##get formated data
        sleep(.5)
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
