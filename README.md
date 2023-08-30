# Ambient Weather API to MQTT service
This project retrieves weather data from ambientwether.net and sends
that data to an MQTT broker for further processing. This software has
been tested with the Ambient Weather Station model WS-2902.

## Installation and Set Up
### Ambient Weather API Credentials
1. Open [Ambientweather.net/account](https://ambientweather.net/account), login, and click on the Create API Key button
2. You can edit the Label and call it AMBIENT_API_KEY, for example
3. In the same API Keys section of the Accounts page, near the bottom, you'll see "Developers: An Application Key is also required for each application that you develop." click on the "click here" link, describe what your application is, and click Create Application Key.
4. Edit the Label for the Application Key and name it AMBIENT_APPLICATION_KEY
5. Note both of these keys for insertion into the service-ambient.ini file
### Software Installation
This assumes a debian style system such as Ubuntu and use the 'pi' user as an example.

1. Copy this repository ```git clone https://github.com/dkoneill/ambient2MQTT.git```
2. Edit ambient2MQTT/service-ambient.ini and set your defaults. Be sure to change YourSiteName and MQTT_TOPIC. This file is read by ambient2MQTT.py on startup. To re-read the file, restart the service.
3. Edit ambient2MQTT/ambient2MQTT.py and change SiteName to match the site name in the service-ambient.ini file.
4. Edit ambient2MQTT/ambient2MQTT.service, which is the systemd service definition, and set appropriate defaults. The ExecStart and WorkingDirectory paths need to be correct for your installation.
5. Install the systemd service
   ``` 
   sudo cp ambient2MQTT/ambient2MQTT.service /etc/systemd/system
   sudo systemctl enable ambient2MQTT
   sudo systemctl start ambient2MQTT
   sudo journalctl -xfu ambient2MQTT.service
   ```
#### Example Systemd ambient2MQTT.service file
```
[Unit]
Description=Ambient Weather API to MQTT service
After=network.service
Wants=network-online.target

[Service]
User=pi
Type=simple
ExecStart=/usr/bin/python3 /home/pi/ambient2MQTT/ambient2MQTT.py
WorkingDirectory=/home/pi/ambient2MQTT
Restart=always
RestartSec=60
[Install]
WantedBy=multi-user.target
```
# Example ambient2MQTT service-ambient.ini file
```
[YourSiteName]
AMBIENT_APPLICATION_KEY=700ae98fcce076756dff9d409a0ffd20
AMBIENT_API_KEY=bc0d62871386c96b53e5d32de5eaff9ba04fdbf775df07f3996330bc53f4abd5
AMBIENT_ENDPOINT=https://api.ambientweather.net/v1
AMBIENT_FREQUENCY=5
MQTT_HOST=mqtt.example.com
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TOPIC=YOURSITENAME/sensor/weather/station1
```
