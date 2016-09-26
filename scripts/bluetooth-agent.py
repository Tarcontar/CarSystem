#!/usr/bin/python

#import os
#import time
#from espeak import espeak

#print " "
#print "starting bluetooth-agent.py ..."

#espeak.synth("starting carSystem ")
#time.sleep(2)


#while True:
#	time.sleep(5)

############################################################################################################################

#!/usr/bin/env python

# Dependencies
#sudo apt-get install -y python-gobject
#sudo apt-get install -y python-smbus
#!/usr/bin/python

# blueagent5.py
# Dependencies: python-gobject (install with e.g. 'sudo apt-get install python-gobject' on Raspian
# Author: Douglas Otwell
# This software is released to the public domain

# The Software is provided "as is" without warranty of any kind, either express or implied, 
# including without limitation any implied warranties of condition, uninterrupted use, 
# merchantability, fitness for a particular purpose, or non-infringement.

import time
import sys
import signal
import dbus
import dbus.service
import dbus.mainloop.glib
import gobject
from optparse import OptionParser

SERVICE_NAME = "org.bluez"
AGENT_IFACE = SERVICE_NAME + '.Agent1'
ADAPTER_IFACE = SERVICE_NAME + '.Adapter1'
DEVICE_IFACE = SERVICE_NAME + '.Device1'
PLAYER_IFACE = SERVICE_NAME + '.MediaPlayer1'
TRANSPORT_IFACE = SERVICE_NAME + '.MediaTransport1'

"""Utility functions from bluezutils.py"""
def getManagedObjects():
	bus = dbus.SystemBus()
	manager = dbus.Interface(bus.get_object("org.bluez", "/"), "org.freedesktop.DBus.ObjectManager")
	return manager.GetManagedObjects()

def findAdapter():
	objects = getManagedObjects();
	bus = dbus.SystemBus()
	for path, ifaces in objects.iteritems():
		adapter = ifaces.get(ADAPTER_IFACE)
		if adapter is None:
			continue
		obj = bus.get_object(SERVICE_NAME, path)
		return dbus.Interface(obj, ADAPTER_IFACE)
	raise Exception("Bluetooth adapter not found")

class BlueAgent(dbus.service.Object):
	AGENT_PATH = "/blueagent5/agent"
	CAPABILITY = "DisplayOnly"
	pin_code = None

	def __init__(self, pin_code):
		"""Initialize gobject, start the LCD, and find any current media players"""
		self.bus = dbus.SystemBus()
		dbus.service.Object.__init__(self, dbus.SystemBus(), BlueAgent.AGENT_PATH)
		self.pin_code = pin_code
		
		self.bus.add_signal_receiver(self.playerHandler,
				bus_name="org.bluez",
				dbus_interface="org.freedesktop.DBus.Properties",
				signal_name="PropertiesChanged",
				path_keyword="path")
				
		self.registerAgent()

		adapter_path = findAdapter().object_path
		self.bus.add_signal_receiver(self.adapterHandler,
				bus_name = "org.bluez",
				path = adapter_path,
				dbus_interface = "org.freedesktop.DBus.Properties",
				signal_name = "PropertiesChanged",
				path_keyword = "path")

		self.findPlayer()

		print("Starting BlueAgent with PIN [{}]".format(self.pin_code))
		
	def start(self):
		"""Start the BluePlayer by running the gobject mainloop()"""
		try:
			mainloop = gobject.MainLoop()
			mainloop.run()
		except:
			self.end()
			
	def findPlayer(self):
		"""Find any current media players and associated device"""
		manager = dbus.Interface(self.bus.get_object("org.bluez", "/"), "org.freedesktop.DBus.ObjectManager")
		objects = manager.GetManagedObjects()

		player_path = None
		transport_path = None
		for path, interfaces in objects.iteritems():
			if PLAYER_IFACE in interfaces:
				player_path = path
			if TRANSPORT_IFACE in interfaces:
				transport_path = path

		if player_path:
			logging.debug("Found player on path [{}]".format(player_path))
			self.connected = True
			self.getPlayer(player_path)
			player_properties = self.player.GetAll(PLAYER_IFACE, dbus_interface="org.freedesktop.DBus.Properties")
			if "Status" in player_properties:
				self.status = player_properties["Status"]
			if "Track" in player_properties:
				self.track = player_properties["Track"]
		else:
			logging.debug("Could not find player")

		if transport_path:
			logging.debug("Found transport on path [{}]".format(player_path))
			self.transport = self.bus.get_object("org.bluez", transport_path)
			logging.debug("Transport [{}] has been set".format(transport_path))
			transport_properties = self.transport.GetAll(TRANSPORT_IFACE, dbus_interface="org.freedesktop.DBus.Properties")
			if "State" in transport_properties:
				self.state = transport_properties["State"]

	def getPlayer(self, path):
		"""Get a media player from a dbus path, and the associated device"""
		self.player = self.bus.get_object("org.bluez", path)
		logging.debug("Player [{}] has been set".format(path))
		device_path = self.player.Get("org.bluez.MediaPlayer1", "Device", dbus_interface="org.freedesktop.DBus.Properties")
		self.getDevice(device_path)

	def getDevice(self, path):
		"""Get a device from a dbus path"""
		self.device = self.bus.get_object("org.bluez", path)
		self.deviceAlias = self.device.Get(DEVICE_IFACE, "Alias", dbus_interface="org.freedesktop.DBus.Properties")

	def playerHandler(self, interface, changed, invalidated, path):
		"""Handle relevant property change signals"""
		logging.debug("Interface [{}] changed [{}] on path [{}]".format(interface, changed, path))
		iface = interface[interface.rfind(".") + 1:]

		if iface == "Device1":
			if "Connected" in changed:
				self.connected = changed["Connected"]
		if iface == "MediaControl1":
			if "Connected" in changed:
				self.connected = changed["Connected"]
				if changed["Connected"]:
					logging.debug("MediaControl is connected [{}] and interface [{}]".format(path, iface))
					self.findPlayer()
		elif iface == "MediaTransport1":
			if "State" in changed:
				logging.debug("State has changed to [{}]".format(changed["State"]))
				self.state = (changed["State"])
			if "Connected" in changed:
				self.connected = changed["Connected"]
		elif iface == "MediaPlayer1":
			if "Track" in changed:
				logging.debug("Track has changed to [{}]".format(changed["Track"]))
				self.track = changed["Track"]
			if "Status" in changed:
				logging.debug("Status has changed to [{}]".format(changed["Status"]))
				self.status = (changed["Status"])

	def next(self):
		self.player.Next(dbus_interface=PLAYER_IFACE)

	def previous(self):
		self.player.Previous(dbus_interface=PLAYER_IFACE)

	def play(self):
		self.player.Play(dbus_interface=PLAYER_IFACE)

	def pause(self):
		self.player.Pause(dbus_interface=PLAYER_IFACE)

	def volumeUp(self):
		self.control.VolumeUp(dbus_interface=CONTROL_IFACE)
		self.transport.VolumeUp(dbus_interface=TRANSPORT_IFACE)

	@dbus.service.method(AGENT_IFACE, in_signature="os", out_signature="")
	def DisplayPinCode(self, device, pincode):
		print("BlueAgent DisplayPinCode invoked")

	@dbus.service.method(AGENT_IFACE, in_signature="ouq", out_signature="")
	def DisplayPasskey(self, device, passkey, entered):
		print("BlueAgent DisplayPasskey invoked")

	@dbus.service.method(AGENT_IFACE, in_signature="o", out_signature="s")
	def RequestPinCode(self, device):
		print("BlueAgent is pairing with device [{}]".format(device))
		self.trustDevice(device)
		return self.pin_code

	@dbus.service.method(AGENT_IFACE, in_signature="ou", out_signature="")
	def RequestConfirmation(self, device, passkey):
		"""Always confirm"""
		print("BlueAgent is pairing with device [{}]".format(device))
		self.trustDevice(device)
		return

	@dbus.service.method(AGENT_IFACE, in_signature="os", out_signature="")
	def AuthorizeService(self, device, uuid):
		"""Always authorize"""
		print("BlueAgent AuthorizeService method invoked")
		return

	@dbus.service.method(AGENT_IFACE, in_signature="o", out_signature="u")
	def RequestPasskey(self, device):
		print("RequestPasskey returns 0")
		return dbus.UInt32(0)

	@dbus.service.method(AGENT_IFACE, in_signature="o", out_signature="")
	def RequestAuthorization(self, device):
		"""Always authorize"""
		print("BlueAgent is authorizing device [{}]".format(self.device))
		return

	@dbus.service.method(AGENT_IFACE, in_signature="", out_signature="")
	def Cancel(self):
		print("BlueAgent pairing request canceled from device [{}]".format(self.device))

	def trustDevice(self, path):
		bus = dbus.SystemBus()
		device_properties = dbus.Interface(bus.get_object(SERVICE_NAME, path), "org.freedesktop.DBus.Properties")
		device_properties.Set(DEVICE_IFACE, "Trusted", True)

	def registerAgent(self):
		bus = dbus.SystemBus()
		manager = dbus.Interface(bus.get_object(SERVICE_NAME, "/org/bluez"), "org.bluez.AgentManager1")
		manager.RegisterAgent(BlueAgent.AGENT_PATH, BlueAgent.CAPABILITY)
		manager.RequestDefaultAgent(BlueAgent.AGENT_PATH)
		print("Blueplayer is registered as a default agent")

	def startPairing(self):
		bus = dbus.SystemBus()
		adapter_path = findAdapter().object_path
		adapter = dbus.Interface(bus.get_object(SERVICE_NAME, adapter_path), "org.freedesktop.DBus.Properties")
		adapter.Set(ADAPTER_IFACE, "Discoverable", True)

		print("BlueAgent is waiting to pair with device")
		
def navHandler(buttons):
	print("Handling navigation for [{}]".format(buttons))
	"""Handle the navigation buttons"""
	if buttons == Lcd.BUTTON_SELECT:
		player.startPairing()
	elif buttons == Lcd.BUTTON_LEFT:
		player.previous()
	elif buttons == Lcd.BUTTON_RIGHT:
		player.next()
	elif buttons == Lcd.BUTTON_UP:
		if player.getStatus() == "playing":
			player.pause()
		else:
			player.play()

bus = None

if __name__ == "__main__":
	pin_code = "0000"
	parser = OptionParser()
	parser.add_option("-p", "--pin", action="store", dest="pin_code", help="PIN code to pair with", metavar="PIN")
	(options, args) = parser.parse_args()

	# use the pin code if provided
	if (options.pin_code):
		pin_code = options.pin_code

	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

	agent = BlueAgent(pin_code)
	agent.registerAsDefault()
	agent.startPairing()

	mainloop = gobject.MainLoop()
	mainloop.run()