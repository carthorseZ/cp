from datetime import datetime
from flask import Flask, render_template, request, redirect
from app import helpers
from . import app


@app.route("/")
def home():
    """Renders the home page."""
    config_dict = helpers.get_config()

    temp = config_dict["temp"]    
    min = config_dict["mintemp"]
    humidity = config_dict["humidity"]

    if (config_dict['heating']=="T"):
        border_heating = "border-danger"
    
    if (config_dict['watering']=="T" ) :
        border_watering = "border-success"

    return render_template('home.html', **locals())

@app.route("/settings")
def settings():
    """Renders the settings page."""    
    config_dict = helpers.get_config()
    print(config_dict)
    return render_template('settings.html', **locals())

@app.route('/settings', methods=['POST'])
def updateSettings():
    MorningTargetTemp = request.form.get('MorningTargetTemp')
    MorningStartTime = request.form.get('MorningStartTime')
    MorningEndTime = request.form.get('MorningEndTime')
    EveningTargetTemp = request.form.get('EveningTargetTemp')
    EveningStartTime = request.form.get('EveningStartTime')
    EveningEndTime = request.form.get('EveningEndTime')
    MinTempThreshold = request.form.get('MinTempThreshold')

    conn, c = helpers.create_db_cursor()
    c.execute("UPDATE config set value='{}' where id='MorningTargetTemp';".format(MorningTargetTemp))
    c.execute("UPDATE config set value='{}' where id='MorningStartTime';".format(MorningStartTime))
    c.execute("UPDATE config set value='{}' where id='MorningEndTime';".format(MorningEndTime))
    c.execute("UPDATE config set value='{}' where id='EveningTargetTemp';".format(EveningTargetTemp))
    c.execute("UPDATE config set value='{}' where id='EveningStartTime';".format(EveningStartTime))
    c.execute("UPDATE config set value='{}' where id='EveningEndTime';".format(EveningEndTime))
    c.execute("UPDATE config set value='{}' where id='MinTempThreshold';".format(MinTempThreshold))
    helpers.commit_and_close_db_connection(conn, c) 
   
    return redirect('/settings')
    
@app.route('/process', methods=['POST'])
def process():
    conn, c = helpers.create_db_cursor()
    #update DB based on button pushed
    button = request.form.get("button")
    if (button=="Water Vegs"):
        c.execute("UPDATE config set value='-1' where id='skip';")
        c.execute("UPDATE config set value='T' where id='watering';")
    elif (button=="Water Berries"):
        c.execute("UPDATE config set value='-2' where id='skip';")
        c.execute("UPDATE config set value='T' where id='watering';")
    elif (button=="Skip One"):
        c.execute("UPDATE config set value='1' where id='skip';")
    elif (button=="Skip Two"):
        c.execute("UPDATE config set value='2' where id='skip';")  
    elif (button=="Heat 1 Hour"):
        c.execute("UPDATE config set value='1' where id='override';")  
        c.execute("UPDATE config set value='T' where id='heating';")
    elif (button=="Heat 2 Hours"):
        c.execute("UPDATE config set value='2' where id='override';")
        c.execute("UPDATE config set value='T' where id='heating';")  
    else:
        print ("button not found")

    helpers.commit_and_close_db_connection(conn, c) 
    return redirect('/')




    

