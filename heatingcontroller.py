#!/usr/bin/env python3
from config import *  
from time import sleep
from datetime import datetime
from grove.gpio import GPIO
import pymysql
from groverelay import GroveRelay
import logging
import helpers


def main():
   
    # Connect to the database.
    conn, c = helpers.create_db_cursor()
        
    relay = GroveRelay(5)

    while True:
        now = datetime.now()
        log_time = datetime.now().strftime("%H.%M.%S")

        c.execute(f"SELECT value from config where id='temp';")
        data = c.fetchone()
        temp = int(data[0])

        c.execute(f"SELECT value from config where id='mintemp';")
        data = c.fetchone()
        mintemp = int(data[0])

        c.execute(f"SELECT value from config where id='humidity';")
        data = c.fetchone()
        humidity = int(data[0])
 
        c.execute(f"SELECT value from config where id='override';")
        data = c.fetchone()
        override = int(data[0])  
        
        values = f"temp {temp}{DEGREE_SIGN} mintemp {mintemp}{DEGREE_SIGN} humidity {humidity}%"
       
        if (override != 0 ):
            c.execute(f"UPDATE config set value='0' where id='override';")
            c.execute(f"UPDATE config set value='T' where id='heating';")
            conn.commit()
            logging.info(f"Manual {override} hour {values}")
            relay.on()
            sleep(override*60*60)
            relay.off()
            c.execute(f"UPDATE config set value='F' where id='heating';")
            conn.commit()
        elif (temp <= mintemp):
            relay.on()
            c.execute(f"UPDATE config set value='T' where id='heating';")
            conn.commit()
            logging.info(f"Below min temp Heating on {values}")
            sleep(MIN_RUN_TIME)       
        else:
            c.execute(f"UPDATE config set value='F' where id='heating';")
            conn.commit()
            relay.off()
            logging.info(f"All G temperature {values}")
            sleep(60)
   
main()
