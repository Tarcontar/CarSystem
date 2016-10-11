#!/bin/bash
# has to run after boot

echo ""
echo "#####"
echo "starting carSystem"
echo "#####"

systemctl start pulseaudio 

sudo python /carSystem/i2c-agent.py &

sudo python /carSystem/bluetooth-agent.py &

#sudo /carSystem/wifi.sh

exit 0