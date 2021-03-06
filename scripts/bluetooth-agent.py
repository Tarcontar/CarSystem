#!/usr/bin/env python

# Dependencies:
# sudo apt-get install -y python-gobject

import time
from time import sleep
from threading import Thread
import signal
import dbus
import dbus.service
import dbus.mainloop.glib
import gobject

SERVICE_NAME = "org.bluez"
AGENT_IFACE = SERVICE_NAME + '.Agent1'
ADAPTER_IFACE = SERVICE_NAME + ".Adapter1"
DEVICE_IFACE = SERVICE_NAME + ".Device1"
PLAYER_IFACE = SERVICE_NAME + '.MediaPlayer1'
TRANSPORT_IFACE = SERVICE_NAME + '.MediaTransport1'

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

class BluePlayer():
	adapter = None
	bus = None
	mainloop = None
	device = None
	deviceAlias = None
	player = None
	connected = None
	state = None
	status = None
	track = []
	
	def __init__(self):
		"""Specify a signal handler, and find any connected media players"""
		gobject.threads_init()
		dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

		self.bus = dbus.SystemBus()

		self.bus.add_signal_receiver(self.playerHandler,
				bus_name="org.bluez",
				dbus_interface="org.freedesktop.DBus.Properties",
				signal_name="PropertiesChanged",
				path_keyword="path")
				
		adapter_path = findAdapter().object_path
		adapter = dbus.Interface(self.bus.get_object(SERVICE_NAME, adapter_path), "org.freedesktop.DBus.Properties")
		adapter.Set(ADAPTER_IFACE, "Discoverable", True)

		self.findPlayer()
		self.updateDisplay()
		
	def update(self):
		player.play()
		while True:
			sleep(5)
			#player.next()
			#print("next")
			#sleep(2)
			#player.pause()
			#sleep(2)
			#player.play()

	def start(self):
		"""Start the BluePlayer by running the gobject Mainloop()"""
		thread = Thread(target = self.update, args = ())
		thread.start()
		#thread.join()

		self.mainloop = gobject.MainLoop()
		self.mainloop.run()
		

	def end(self):
		"""Stop the gobject Mainloop()"""
		if (self.mainloop):
			self.mainloop.quit();

	def findPlayer(self):
		"""Find any current media players and associated device"""
		manager = dbus.Interface(self.bus.get_object("org.bluez", "/"), "org.freedesktop.DBus.ObjectManager")
		objects = manager.GetManagedObjects()

		player_path = None
		for path, interfaces in objects.iteritems():
			if PLAYER_IFACE in interfaces:
				player_path = path
				break

		if player_path:
			self.connected = True
			self.getPlayer(player_path)
			player_properties = self.player.GetAll(PLAYER_IFACE, dbus_interface="org.freedesktop.DBus.Properties")
			if "Status" in player_properties:
				self.status = player_properties["Status"]
			if "Track" in player_properties:
				self.track = player_properties["Track"]

	def getPlayer(self, path):
		"""Get a media player from a dbus path, and the associated device"""
		self.player = self.bus.get_object("org.bluez", path)
		device_path = self.player.Get("org.bluez.MediaPlayer1", "Device", dbus_interface="org.freedesktop.DBus.Properties")
		self.getDevice(device_path)

	def getDevice(self, path):
		"""Get a device from a dbus path"""
		self.device = self.bus.get_object("org.bluez", path)
		self.deviceAlias = self.device.Get(DEVICE_IFACE, "Alias", dbus_interface="org.freedesktop.DBus.Properties")
		print("Connected with: " + self.deviceAlias)
		#set adapter to invisible??

	def playerHandler(self, interface, changed, invalidated, path):
		"""Handle relevant property change signals"""
		iface = interface[interface.rfind(".") + 1:]
		#print("Interface: {}; changed: {}".format(iface, changed))

		if iface == "Device1":
			if "Connected" in changed:
				self.connected = changed["Connected"]
		elif iface == "MediaControl1":
			if "Connected" in changed:
				self.connected = changed["Connected"]
				if changed["Connected"]:
					self.findPlayer()
		elif iface == "MediaPlayer1":
			if "Track" in changed:
				self.track = changed["Track"]
				self.updateDisplay()
			if "Status" in changed:
				self.status = (changed["Status"])
				
	def updateDisplay(self):
		if self.player:
			if "Artist" in self.track:
				print(self.track["Artist"])
				print("teste")
			if "Title" in self.track:
				print(self.track["Title"])
		else:
			print("Waiting for media player")

	def next(self):
		if self.player:
			self.player.Next(dbus_interface=PLAYER_IFACE)

	def previous(self):
		if self.player:
			self.player.Previous(dbus_interface=PLAYER_IFACE)

	def play(self):
		if self.player:
			self.player.Play(dbus_interface=PLAYER_IFACE)

	def pause(self):
		if self.player:
			self.player.Pause(dbus_interface=PLAYER_IFACE)

if __name__ == "__main__":
	player = None

	try:
		player = BluePlayer()
		player.start()
	except KeyboardInterrupt as ex:
		print("\nBluePlayer cancelled by user")
	except Exception as ex:
		print("How embarrassing. The following error occurred {}".format(ex))
	finally:
		if player: player.end()