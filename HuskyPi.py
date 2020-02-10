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

I2C_SLAVE=0x0703 #not sure what this is

COMMAND_REQUEST=0x20
COMMAND_REQUEST_BLOCKS=0x21
COMMAND_REQUEST_ARROWS=0x22
COMMAND_REQUEST_LEARNED=0x23
COMMAND_REQUEST_ARROWS_LEARNED=0x25
COMMAND_REQUEST_BY_ID=0x26
COMMAND_REQUEST_BLOCKS_BY_ID=0x27
COMMAND_REQUEST_ARROWS_BY_ID=0x28
COMMAND_RETURN_INFO=b'\x29'
COMMAND_RETURN_BLOCK=b'\x2a'
COMMAND_RETURN_ARROW=b'\x2b'
COMMAND_REQUEST_KNOCK=0x2c
COMMAND_REQUEST_ALGORITHM=0x2d
COMMAND_RETURN_OK=b'\x2e'

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
    def __init__(self,mode=SERIAL,baud=9600,device=0x32,bus=1):
        '''initialise huskylens
            mode SERIAL/I2C
            options
            baud    serial baudrate
            bus     I2C bus
            addr    I2C addr
            defaults 9600 baud bus 1 addr 32
            '''
        self.mode=mode
        if mode:    #serial initialisation 
            self.port = serial.Serial("/dev/ttyS0", baudrate=baud, timeout=3.0)
            
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
            print('msg-sent:%s',data)
        else:
            return self.fw.write(bytes(data))

    def read(self,length,timeout=.1):
        '''read lenth bytes from husklens
        timeout on serial port raises HLTimeoutError'''
        if self.mode:
            result=''
            timeout=time.time()
            while result== '':
                data=self.port.read(length)
                if data !="":
                    result=data
                    break
                if time.time()-timeout >timeout:
                    raise HLTimeoutError('Timeout')
                    break
                    
                
        else:
            result = self.fr.read(length)
        return result

    def read_response(self):
        '''get full response packet from huskylens
        if data does not conform raise readError'''
        for x in range(3):
            char=self.read(1)

            if ord(char)!= self.PREFIX[x]:
                raise HLProtocolError(x)
                
        length=ord(self.read(1))
        cmd=self.read(1)
        if length>0:
            data=self.read(length)
        else:
            data=None
            
        csum=self.read(1)
##  Checksum check should go here!
        return cmd,data
            
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
        
    def execute(self):
        self.write(self.command(COMMAND_REQUEST)) #request data from husky
        cmd,data=self.read_response()
        if cmd !=COMMAND_RETURN_INFO:
            print (cmd,data)
            raise HLError('Expected Command Info Packet')
        packets=data[0]+data[1]*256    #Number of blocks & arrows
        ids=data[2]+data[3]*256  #number of IDs
        print("Packets=%s,id's=%s"%(packets,ids))
        response=[]
        while packets >0:
            self.write(self.command(COMMAND_REQUEST))
            #time.sleep(.1)
            response.append(self.read_response())
            packets -=1
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

def main(args):
    hl=HuskyLens(mode=SERIAL)
    for x in range (2):
        while True:
            print('Read line tracking')
            try:
                response=hl.execute()
                for cmd,data in response:
                    print('command:%s Data :'%hex(ord(cmd)),end=" ")
                    for byte in data:
                        print(hex(byte),end=':')
                    print()
                    break
            except HLError:
                print('ok try again')
    return 0

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
