#!/bin/bash
# has to run after boot

echo ""
echo "#####"
echo "starting carSystem"
echo "#####"

systemctl start pulseaudio 

#sudo python bluetooth-agent.py &

sudo python i2c-agent.py &

exit 0