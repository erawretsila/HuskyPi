#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  HuskySerial.py
#  
#  Copyright 2020  <pi@HuskyTest>
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
import io
import fcntl
 
import serial
import time

VERSION=0.5

I2C_SLAVE=0x0703 #I2C interface ID/location?

COMMAND_REQUEST=0x20
COMMAND_REQUEST_BLOCKS=0x21
COMMAND_REQUEST_ARROWS=0x22
COMMAND_REQUEST_LEARNED=0x23
COMMAND_REQUEST_ARROWS_LEARNED=0x25
COMMAND_REQUEST_BY_ID=0x26
COMMAND_REQUEST_BLOCKS_BY_ID=0x27
COMMAND_REQUEST_ARROWS_BY_ID=0x28
COMMAND_RETURN_INFO=0x29
COMMAND_RETURN_BLOCK=0x2a
COMMAND_RETURN_ARROW=0x2b
COMMAND_REQUEST_KNOCK=0x2c
COMMAND_REQUEST_ALGORITHM=0x2d
COMMAND_RETURN_OK=0x2e

ALGORITHM_FACE_REC=[0x00,0x00]
ALGORITHM_OBJECT_TRACK=[0x01,0x00]
ALGORITHM_OBJECT_REC=[0x02,0x00]
ALGORITHM_LINE_TRACK=[0x03,0x00]
ALGORITHM_COLOUR_REC=[0x04,0x00]
ALGORITHM_TAG_REC=[0x05,0x00]
ALGORITHM_OBJECT_CLASS=[0x06,0x00]

SERIAL=True
I2C=False

class HLError(Exception):
    pass
    
class HLTimeoutError(HLError):
    pass
    
class HLProtocolError(HLError):
    pass

class HuskyLens(object):
    ''' library for huskylens vission processor'''
    PREFIX=[0x55,0xaa,0x11]
    def __init__(self,mode=SERIAL,port='/dev/ttyS0',baud=9600,device=0x32,bus=1,debug=False):
        '''initialise huskylens
            mode SERIAL/I2C
            options
            baud    serial baudrate
            bus     I2C bus
            addr    I2C addr
            defaults 9600 baud bus 1 addr 32
            '''
        self.mode=mode
        self.debug=debug
        if mode:    #serial initialisation 
            self.port = serial.Serial(port, baudrate=baud, timeout=3.0)
            
        else:   #I2C initialisation
            
            self.fr = io.open("/dev/i2c-"+str(bus), "rb", buffering=0)
            self.fw = io.open("/dev/i2c-"+str(bus), "wb", buffering=0)

              # set device address

            fcntl.ioctl(self.fr, I2C_SLAVE, device)
            fcntl.ioctl(self.fw, I2C_SLAVE, device)
               
    def write(self,data):
        '''Send stream of data to huskylens'''
        if self.mode:
            pass
            self.port.write(data)
        else:
            self.fw.write(bytes(data))
        self.dump(data)
        return
        
    def read(self,length,timeout=.1):
        '''read lenth bytes from husklens
        timeout on serial port raises HLTimeoutError
        Failure to confirm to HuskyLens protocol raises 
        HLProtocolError'''
        if self.mode:
            result=self.port.read(length)
            if len(result)< length:
                raise HLTimeoutError
        else:
            result = self.fr.read(length)
        #check mesg prefix
        for i,byte in enumerate(self.PREFIX):
            if byte !=result[i]:
                raise HLProtocolError(result)
        #check checksum :-)
        csum=0
        for x in result[:-1]:
            csum+=x
        if csum&255!=result[-1]:
            raise HLProtocolError(result)
        return result

    def read_response(self,length=16):
        '''get full response packet from huskylens
        if data does not conform raise readError'''
        packet=self.read(length)
        self.dump(packet)
        cmd=packet[4]
        data=[]
        count=0
        if cmd==COMMAND_RETURN_OK:
            return packet
        if cmd==COMMAND_RETURN_INFO:
            count=packet[5]
        if count >0:
            for x in range(count):
                packet=self.read(length)
                self.dump(packet)
                data.append(packet)
        return data
            
    def command(self,cmd,data=None):
        '''create Huskylens command message'''
        if not data:
            data=[]
        msg=[]
        chksum=0
#   build Huskylens command
        length=len(data)
        msg += self.PREFIX+[length]+[cmd]+data
#   calculate checksum        
        for x in msg:
            chksum+=x
        msg +=[chksum & 255]
        return msg

    def knock(self):
        '''check for active huskylens'''
        self.write(self.command(COMMAND_REQUEST_KNOCK))
        response=self.read(6)
        if response != bytes(self.PREFIX+[00,COMMAND_RETURN_OK,0x3e]):
            raise HLProtocolError(response)
        
    def set_mode(self,algorithm):
        '''Set huskylens detaction mode
        raise HLProtocolError if fails'''
        self.write(self.command(COMMAND_REQUEST_ALGORITHM,algorithm))
        response=self.read_response(6)
        if response != bytes(self.PREFIX+[00,COMMAND_RETURN_OK,0x3e]):
            raise HLProtocolError(response)
        
    def execute(self, decode=False):
        '''reqests data for husky lens
        returns a list of 0 or more detected items in the format
        type,(start/center co-ordinates),(end/Height + width)
        type is ether 0x2a for block (center & height + width)
        or  ox2b for Line (start coords, end coords)
        '''
        self.write(self.command(COMMAND_REQUEST))
        response= self.read_response()
        if format:
            
            for i,data in enumerate(response):
                start=(data[5]+data[6]*256,data[7]+data[8]*256)
                end=(data[9]+data[10]*256,data[11]+data[12]*256)
                response[i]=[data[4],start,end]
        return response
        
    def close(self):
        '''Close husky lens connection'''
        if mode:
#   close serial?
            pass
        else:
#close I2C
            self.fw.close()
            self.fr.close()

    def dump(self,packet):
        '''print a hex dump of 'packet'''
        if self.debug:
            print ("Packet :",end='')
            for x in packet:
                print(hex(x),end=":")
            print()
        

def main(args):
    hl=HuskyLens(mode=I2C,debug=False)
    hl.knock()
    hl.set_mode(ALGORITHM_LINE_TRACK)
    time.sleep(.2)
    for x in range (10):
        print('Read line tracking')
        try:
            response=hl.execute(format=True)
            print(response)
        except HLError:
            print("Something Fucked")
        time.sleep(0.5)
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
