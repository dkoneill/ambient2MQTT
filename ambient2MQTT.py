#!/usr/bin/python3

from systemd.journal import JournalHandler
from ambient_api.ambientapi import AmbientAPI
import time
import configparser
import paho.mqtt.client as mqtt
import os
import json
import logging


# Change these to match your configuration

ConfigFile = "service-ambient.ini"
SiteName = "YourSiteName"


def when(ts=0):
    if not ts:
        ts = time.time()
    return time.strftime("%D %H:%M:%S  ",time.localtime(ts))

# Intialize Ambient Weather API connection object and retrieve device info
def AmbientAPIInit():
    Ambient_api = AmbientAPI(AMBIENT_ENDPOINT=cfg['AMBIENT_APPLICATION_KEY'],
                         AMBIENT_API_KEY=cfg['AMBIENT_API_KEY'],
                         AMBIENT_APPLICATION_KEY=cfg['AMBIENT_APPLICATION_KEY'] )
    Ambient_devices = Ambient_api.get_devices()
    StationDevice = Ambient_devices[0]
    time.sleep(2)     # Ambient Weather API rate limits to 1 call / sec so sleep first :-)
    return StationDevice

class Ambient_MQTT_Service (mqtt.Client):
    def on_connect(self, mqttc, obj, flags, rc):
        log.debug("on_connect rc:"+str(rc))
        
    def on_message(self, mqttc, obj, flags):
        log.debug("Unsolicited message?")
        return
    
    def service_reset(self,message):
        global sink
        sink = {}
        
    def run(self):
        if (cfg['MQTT_USERNAME'] and cfg['MQTT_PASSWORD']):
            self.username_pw_set(cfg['MQTT_USERNAME'], cfg['MQTT_PASSWORD']) # not tested
        self.connect(cfg['MQTT_HOST'], MQTT_PORT, 60)
        self.subscribe("$SYS/#", 0)


# Main

log = logging.getLogger('root')
log.addHandler(JournalHandler())
log.setLevel(logging.INFO)

# Read the service configuration file
config = configparser.ConfigParser()
config.read(ConfigFile)
# re-read integer values as configparser returns unicode strings
try: 
    MQTT_PORT = config.getint(SiteName, 'MQTT_PORT');
except:
    MQTT_PORT = 1883

try:
    Frequency = config.getint(SiteName, 'AMBIENT_FREQUENCY');
except:
    Frequency = 10

if SiteName not in config.sections():
    log.warn("Site {} is not listed in {}".format(SiteName, ConfigFile))
    exit()

cfg=config[SiteName]
if not (cfg['AMBIENT_APPLICATION_KEY']
        and cfg['AMBIENT_API_KEY']
        and cfg['AMBIENT_ENDPOINT']
        and cfg['MQTT_HOST']
        and cfg['MQTT_TOPIC'] ):
    log.warn("Site {} is missing settings in {}".format(SiteName, ConfigFile))
    exit()

# Start MQTT service and loop

MQTT_service = Ambient_MQTT_Service("ambient2MQTT")
MQTT_service.run()
MQTT_service.loop_start()

# Sample weather data from device
sample_data = {
   "dateutc":1636692300000,
   "tempinf":69.3,    # indoor temp in F
   "humidityin":53,   # indoor humidity
   "baromrelin":29.986,  # relative pressure in Hg
   "baromabsin":30.033,  # absolute pressure in Hg
   "tempf":68.4,         # outdoor temp in F
   "battout":1,          # outdoor battery status 1=OK, 0=Low
   "humidity":54,        # outdoor humidity
   "winddir":21,         # instantaneous wind direction 0-360
   "windspeedmph":0.9,   # instantaneous wind speed in mph
   "windgustmph":1.1,    # wind gust in mph
   "maxdailygust":15.9,  # max daily wind gust in mph
   "hourlyrainin":0,     # hourly rain inches/hr
   "eventrainin":0,      # cmmulative inches of rain for entire event
   "dailyrainin":0,      # cumulative inches of rain for the day
   "weeklyrainin":0,     # cumulative inches of rain for the week
   "monthlyrainin":0,    # cumulative inches of rain for the month
   "totalrainin":6.563,  # cumulative inches of rain since last factory reset
   "solarradiation":0,   # instantaneous solar radiation in W/m^2
   "uv":0,               # Ultra-Violet radiation index
   "feelsLike":67.48,    # outdoor feels-like temperature in F
   "dewPoint":51.1,      # outdoor dew point temperature in F
   "feelsLikein":68.4,   # indoor feels-like temperature in F
   "dewPointin":51.4,    # indoor dew point temperature in F
   "lastRain":"2021-10-26T00:57:00.000Z",  # date and time of last rain event
   "loc":"ambient-prod-45",                # ??
   "date":"2021-11-12T04:45:00.000Z"       # date time string
}

delay = 60 * Frequency
    
AmbientAPIhealth = False

while True:
    while not AmbientAPIhealth:
        try:
            StationDevice = AmbientAPIInit()
            log.info(when()+"Ambient Weather API initialized")
            AmbientAPIhealth = True
        except:
            log.warn(when()+"Ambient Weather API could not be initialized")
            time.sleep(delay)


    StationData = []
    try:
        StationData = StationDevice.get_data(limit=1)
    except:
        AmbientAPIhealth = False
        log.warn(when()+"Ambient Weather API failed, forcing restart")

    if AmbientAPIhealth:
        try:
            log.info(when()+"At {} the outdoor temperature was {:3.2f}F".format(StationData[0]['dateutc'],StationData[0]['tempf']))
            MQTT_service.publish(cfg['MQTT_TOPIC'], json.dumps( StationData[0] ) )
        except:
            log.warn(when()+"Data retrieval error. Continuing...");
        
        time.sleep(delay)
