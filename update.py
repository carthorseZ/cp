#!/usr/bin/env python3
import logging
from config import *
from time import sleep
import seeed_dht
from datetime import datetime
#from grove.gpio import GPIO
#from groverelay import GroveRelay
import helpers

def main():
    sensor = seeed_dht.DHT("11", 12)
#    relay = GroveRelay(5)

    conn, c = helpers.create_db_cursor()
      
    while True:
        sleep(60)
        now = datetime.now()
        humidity, temp = sensor.read()
        #humidity = 20 #temporarily hard code values for testing
        #temp = 20  #temporarily hard code values for testing

        config_dict = helpers.get_config()
        MorningStartTime = int(config_dict["MorningStartTime"])
        MorningEndTime = int(config_dict["MorningEndTime"])
        EveningStartTime = int(config_dict["EveningStartTime"])
        EveningEndTime = int(config_dict["EveningEndTime"])
        MorningTargetTemp = int(config_dict["MorningTargetTemp"])
        EveningTargetTemp = int(config_dict["EveningTargetTemp"])
        MinTempThreshold = int(config_dict["MinTempThreshold"])
        override = config_dict["override"]
      
        if (now.hour >= MorningStartTime and now.hour < MorningEndTime):
            mintemp = MorningTargetTemp
        elif (now.hour >= EveningStartTime and now.hour < EveningEndTime):
            mintemp = EveningTargetTemp
        else:
            mintemp = MinTempThreshold
        
        c.execute(f"UPDATE config set value='{mintemp}' where id='mintemp';")
        c.execute(f"UPDATE config set value='{temp}' where id='temp';")
        c.execute(f"UPDATE config set value='{humidity}' where id='humidity';")
        conn.commit()
        logging.info(f"temp {temp}{DEGREE_SIGN} mintemp {mintemp}{DEGREE_SIGN} humidity {humidity}%" )
   
main()
