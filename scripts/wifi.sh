#!/bin/bash

source config.sh

createAdHocNetwork()
{
	echo "Creating ad-hoc network"
	sudo ifconfig wlan0 up
	sudo iwconfig wlan0 mode ad-hoc
	#sudo iwconfig wlan0 key aaaaa11111 #WEP key
	sudo iwconfig wlan0 essid "RPi" #SSID
	sudo ifconfig wlan0 192.168.3.100 netmask 255.255.255.0 
	sudo /usr/sbin/dhcpd wlan0
	echo "Ad-hoc network created"
}

echo "================================="
echo "RPi Network Conf Bootstrapper 0.1"
echo "================================="
echo "Scanning for known WiFi networks"
connected=false
for ssid in "${ssids[@]}"
do
	if iwlist wlan0 scan | grep $ssid > /dev/null
	then
		echo "Connected to WiFi " $ssid
		sudo ifdown wlan0
		#connected=true
		break
	else
		echo "Not in range, WiFi with SSID:" $ssid
	fi
done

if ! $connected; then
	createAdHocNetwork
fi

exit 0
			
			