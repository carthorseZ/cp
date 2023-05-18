#!/usr/bin/env python3
import logging
from config import *
from time import sleep
from datetime import datetime
import random
import helpers

#import seeed_dht
#from grove.gpio import GPIO
#from groverelay import GroveRelay

def main():
    sleep(5)
    #sensor = seeed_dht.DHT("11", 12)
#    relay = GroveRelay(5)

    conn, c = helpers.create_db_cursor()

    outsideTempTimer = 15
      
    while True:
        sleep(60)
        now = datetime.now()
        humidity, temp =  10,10 #sensor.read()

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

        if (outsideTempTimer >= 15 and now.hour >= 4 and now.hour < 23):
            outsideTemp = helpers.record_outsideTemp()
            outsideTempTimer = 0
        else:
            outsideTemp = '?'
            if (random.randint(1,10) > 1):
                 outsideTempTimer = outsideTempTimer + 1
        
        logging.info(f"temp {temp}{DEGREE_SIGN} mintemp {mintemp}{DEGREE_SIGN} humidity {humidity}% outsideTemp {outsideTemp}{DEGREE_SIGN}" )
   
main()