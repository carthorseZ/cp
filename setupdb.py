#!/usr/bin/env python3
import config
import helpers

# Connect to the database.
conn, c = helpers.create_db_cursor()

#create database
c.execute(f'CREATE DATABASE IF NOT EXISTS {config.DATABASE};')

# Drop tables
c.execute("DROP TABLE IF EXISTS MoistureReading;")
c.execute("DROP TABLE IF EXISTS Forecast")
c.execute("DROP TABLE IF EXISTS config")

# Create tables
c.execute(
    "CREATE TABLE MoistureReading (RecordingID int, RecordID int, DateRecorded datetime, AnalogMoisture int, SoilMoisture int, Humidity int);"
)
c.execute(
    "CREATE TABLE Forecast (ForecastID int, RecordID int, DateRecorded datetime, rain float);"
)

c.execute("CREATE TABLE config (id varchar(20), value varchar(20) )")
c.execute("ALTER TABLE config ADD UNIQUE ID_Index (`id`);")
c.execute("INSERT INTO config VALUES ('skip', -1)")
c.execute("INSERT INTO config VALUES ('version', 1)")
c.execute("INSERT INTO config VALUES ('override', 1)")
c.execute("INSERT INTO config VALUES ('temp', 20)")
c.execute("INSERT INTO config VALUES ('outsideTemp', 18)")
c.execute("INSERT INTO config VALUES ('humidity', 1)")
c.execute("INSERT INTO config VALUES ('mintemp', 10)")
c.execute("INSERT INTO config VALUES ('heating', 'F')")
c.execute("INSERT INTO config VALUES ('watering', 'F')")

c.execute("INSERT INTO config VALUES ('MorningStartTime', 5)")
c.execute("INSERT INTO config VALUES ('MorningEndTime', 6)")
c.execute("INSERT INTO config VALUES ('EveningStartTime', '18')")
c.execute("INSERT INTO config VALUES ('EveningEndTime', '21')")

c.execute("INSERT INTO config VALUES ('MorningTargetTemp', '15')")
c.execute("INSERT INTO config VALUES ('EveningTargetTemp', '18')")
c.execute("INSERT INTO config VALUES ('MinTempThreshold', '10')")
c.execute("INSERT INTO config VALUES ('Temp', '10')")

helpers.commit_and_close_db_connection(conn, c)

