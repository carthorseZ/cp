#!/usr/bin/env python3
"""Helper functions
"""
# Importing configeration
import logging
from config import *    #import configuration variables

# Importing modules
from datetime import datetime # To obtain current date and time
from numpy import interp  # To scale and inverse values
from time import sleep  # To add delay
import RPi.GPIO as GPIO  # To communicate with the pi GPIO ports 
import pymysql  #connect and use Mysql DB
from random import randint  # generate random number for testing
import sys  # to access arguments
from selenium import webdriver  #navigate to page and download
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup #search and return required content from page
from datetime import datetime # obtain and format dates and time
from os import popen
import os

#setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{LOGDIR}{datetime.date(datetime.now())}.txt'),
        logging.StreamHandler()
    ]
)

def get_config():
    """gets the config from the database and returns a dictionary
    """
    conn = create_db_connection()
    c = conn.cursor() 
    c.execute("select * from config;")
    result = c.fetchall()
    config_dict = {}
    for x in result:
        config_dict.update({x[0] : x[1]})
    c.close()
    conn.close()
    return config_dict

def record_forecast(configlocation="queenstown"):
    """gets the metservice forecast for the next 24 hours based on location provided
    saves in a database
     Keyword arguments:
            location -- valid metservice city (default queenstown)
    """
    log_and_notify("Forecast Recording Started")

    # Connect to the database.
    conn = pymysql.connect(db=DATABASE,
        user=USER,
        passwd=PASSWD,
        host=HOST)
    c = conn.cursor()
    
    # Generate ForecastID
    c.execute(f"SELECT MAX(ForecastID) from Forecast;")
    data = c.fetchone()
    if not data[0]:
        forecast_id = 1
    else:
        forecast_id = int(data[0]) + 1
        
    #Setup chrome driver to connect to the site
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome("/usr/lib/chromium-browser/chromedriver", options=chrome_options)
    url = "https://www.metservice.com/towns-cities/locations/" + LOCATION
    
    #connect to webpage download and format the content
    driver.get(url)
    content = driver.page_source
    soup = BeautifulSoup(content, "html.parser")

    #find all the lines which contain the data we want
    p_lines = soup.findAll('p', attrs={'class': 'small u-mT-0 u-mB-0'})

    #remove actual rainfall today and other unwanted lines keeping only 2 days of forecast
    hour_of_Day = datetime.now().strftime("%H")
    start_line = 4 + int(hour_of_Day)
    end_line = start_line + 24
    forecast_lines = p_lines[start_line:end_line]
    
    count = 1
    for f in forecast_lines:
        f_float = float(f.text)
        c.execute(f"INSERT INTO Forecast VALUES ({forecast_id},{count},now(),{f_float})")
        conn.commit()
        count += 1

    log_and_notify("Forecast Recording Ended")
    
def get_forecast():
    """returns the latest forecast
    """
    # Connect to the database.
    conn = pymysql.connect(db=DATABASE,
        user=USER,
        passwd=PASSWD,
        host=HOST)
    c = conn.cursor()

    #get latest forecast
    c.execute(f"SELECT rain FROM Forecast WHERE ForecastID = (SELECT MAX(ForecastID) from Forecast);")
    forecasts = [item[0] for item in c.fetchall()]
    

    return forecasts


def measure_moisture(measurementNumber = 1,measurementDelay = 1.0):
    """Reads the moisture levels and saves in a database  
        Keyword arguments:
            measurementNumber -- How many measurements to take (default 5)
            measurementDelay -- Delay between measurements (default 1.0)
    """
    
    # Connect to the database.
    conn = pymysql.connect(db=DATABASE,
        user=USER,
        passwd=PASSWD,
        host=HOST)
    c = conn.cursor()
    
    # Generate RecordingID
    c.execute(f"SELECT MAX(RecordingID) from MoistureReading;")
    data = c.fetchone()
    if not data[0]:
        RecordingID = 1
    else:
        RecordingID = int(data[0]) + 1

    # Start SPI connection between GPIO ports and A2D convertor
    spi = spidev.SpiDev()
    spi.open(0, 0)

    # Read the MCP3008 analog to digital converter data
    def analogInput(channel):
  #      return randint(407, 792)  ##used for testing without sensor
        spi.max_speed_hz = 1350000
        adc = spi.xfer2([1, (8 + channel) << 4, 0])
        data = ((adc[1] & 3) << 8) + adc[2]
        return data

    # Measure and save
    total_soil_moisture = 0.0
    for count in range(1, measurementNumber+1):
        analog_moisture = analogInput(0)  # Reading from CH0
        soil_moisture = int(interp(analog_moisture, [407, 792],[100, 0]))  # 0=dry 100=wet
        humidity = int( interp(analog_moisture, [407, 792], [100, 50]))  #calibration to an apprioximation of humidity
        print("Moisture:{0}% Analog:{1}".format(soil_moisture, analog_moisture))
        c.execute(
            f"INSERT INTO MoistureReading VALUES ({RecordingID},{count},now(),{analog_moisture},{soil_moisture},{humidity})"
        )
        conn.commit()
        total_soil_moisture += soil_moisture
        sleep(measurementDelay)

    #return average
    return int(total_soil_moisture/measurementNumber)


def open_valve(watering_time=1, control_pin=15):
    
    # Connect to the database.
    conn = pymysql.connect(db=DATABASE,
        user=USER,
        passwd=PASSWD,
        host=HOST)
    c = conn.cursor()
         
    log_and_notify(f"Watering started for {watering_time} mins using pin {control_pin}")
    c.execute(f"UPDATE config set value='T' where id='watering';")
    conn.commit()
        
    watering_time=watering_time * 60     #convert to seconds
    GPIO.setwarnings(False)              #stop channel in use warning    
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(control_pin,GPIO.OUT)
    GPIO.output(control_pin,GPIO.HIGH)

    sleep(watering_time)

    GPIO.output(control_pin,GPIO.LOW)
    GPIO.cleanup()
    
    log_and_notify(f"Watering ended")
    c.execute(f"UPDATE config set value='F' where id='watering';")
    conn.commit()

def log_and_notify(message, important=True):
    logging.info(message)

    #email Send notification
    if (PROD and important ):
        for email in NOTIFICATION_LIST:
            command = f"echo '{message}' | msmtp {email}"
            popen(command)  

def create_db_connection():
    conn: None
    try:
        conn = pymysql.connect(
        db=DATABASE,    
        user=USER,
        passwd=PASSWD,
        host='localhost')
    except logging.error as err:
        print(f"Error: '{err}'")
    return conn

def create_db_cursor():
    conn = create_db_connection()
    cursor = conn.cursor()
    return conn, cursor

def commit_and_close_db_connection(conn, cursor):
    conn.commit()
    cursor.close()
    conn.close()

def record_outsideTemp():

    try:        
        #Setup chrome driver to connect to the site
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome("/usr/lib/chromium-browser/chromedriver", options=chrome_options)
        url = "https://www.wunderground.com/dashboard/pws/IARROW11"
        
        #connect to webpage download and format the content
        driver.get(url)
        content = driver.page_source
        soup = BeautifulSoup(content, "html.parser")

        #find all the lines which contain the data we want
        #p_lines = soup.findAll('p', attrs={'class': 'wu-value wu-value-to'})
        tempHTML = soup.find(class_ ='current-temp')
        tempint = int(tempHTML.text.strip()[:-1]) #removes the leading and trailing spaces and degree symbol
 
        outsideTemp = int((tempint -32) * 5/9)


    except Exception as e:
        logging.critical(f"Error getting outside temp: {e}")
        outsideTemp = -99

    finally:
        conn, c = create_db_cursor()
        c.execute(f"UPDATE config set value='{outsideTemp}' where id='outsideTemp';")
        commit_and_close_db_connection(conn, c)

    return outsideTemp

#test functions
#print(record_outsideTemp())
#open_valve()
#measure_moisture()
#record_forecast()
#record_outsideTemp()