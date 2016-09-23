#!/usr/bin/python

import smbus
import time
import os

print " "
print "starting i2c-agent.py ..."

bus = smbus.SMBus(1)

address = 0x04 # address of the arduino nano slave

def writeNumber(value):
	try:
		bus.write_byte(address, value)
		#print "send value ", value
	except IOError:
		#print "... slave not responding"
		return 0
	return 1
	
def readData():
	try:
		data = bus.read_byte(address)
		#print "received data: ", data
		return data
	except IOError:
		#print "... slave not responding"
		return 0
	return 1
	
while True:
	var = 1
	writeNumber(var) # tell the slave we are alive
	time.sleep(1)
	
	number = readData()
	
	if (number == 0):
		print "*** we have to go to sleep ***"
		os.system("sudo halt")