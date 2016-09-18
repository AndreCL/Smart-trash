# Main flask class

import StringIO
import datetime
import os

import matplotlib.pyplot as plt
import pygal
from flask import Flask, Markup, render_template, redirect, request, jsonify, send_file, abort
from flask_googlemaps import GoogleMaps
from pygal.style import DarkSolarizedStyle

from datahandler import Datahandler
from login import Login

app = Flask(__name__)
GoogleMaps(app)
login_state = Login()
screennum = 0
data_handler = Datahandler()
# Update the version here:
version = "1.60606a"
selected_sensor = 0

@app.route('/')
def index():
    title = "Smarcity Login"
    logtitle = "Login - Dashboard"
    return render_template('index.html', title=title, logtitle=logtitle)


@app.route('/login', methods=['POST'])
def login():
    user = request.form['user']
    password = request.form['password']

    result = login_state.log_in(user=user, password=password)

    if result:
        return redirect('/map_main')  # Change to test other screens
    else:
        return redirect('/')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        result = login_state.log_out()
        if result:
            return redirect('/')
    else:
        result = login_state.log_out()
        if result:
            return redirect('/')

# Todo: Update this
@app.route('/map_main')
def map_main():
    # Make sure that user is logged in
    if not login_state.log_state():
        return redirect('/')

    title_dashboard = 'Smarcity'
    user = login_state.current_user
    permission = login_state.current_usergroup


    #Temperature data
    temperature = data_handler.get_temp_data_latest()

    data = data_handler.load_latest_data(2)
    #current_state = Markup(temp)

    # tab we in
    screennum = 3
    return render_template('start.html', title=title_dashboard, user=user, screennum=screennum,
                           permission=permission, version=version, data=data, icon=temperature[0],
                           desc_icon = temperature[1], temperature = temperature[2].decode("utf8"), humidity = temperature[3],
                           wind_direction_cardinal = temperature[4], wind_speed= temperature[5])

# Dynamically updating the page
@app.route('/get_values', methods= ['GET'])
def get_values():

    #Update DB
    #data_handler.save_new_data()
    #data_handler.save_new_data_old()

    # Get data
    temp = data_handler.load_all_data(1)
    all_data = Markup(temp)
    temp = data_handler.load_latest_data(1)
    current_state = Markup(temp)
    time_now = data_handler.gettime()

    return jsonify(time_now=str(time_now), all_data=all_data, current_state=current_state)


@app.route('/dashboard')
def dashboard():
    # Make sure that user is logged in
    if not login_state.log_state():
        return redirect('/')

    title_dashboard = 'Smarcity'
    permission = login_state.current_usergroup

    #Update DB
    #data_handler.save_new_data()

    # Get data
    temp = data_handler.load_all_data(1)
    all_data = Markup(temp)
    temp = data_handler.load_latest_data(1)
    current_state = Markup(temp)
    time_now = data_handler.gettime()

    # tab we in
    screennum = 0
    return render_template('start.html', title=title_dashboard, screennum=screennum,
                           current_state=current_state, all_data=all_data, permission=permission, version=version, time_now=time_now)


@app.route('/sensor/<name>')
def sensor(name):
    # Make sure that user is logged in
    if name < 1:
        name = data_handler.get_sensor_ids()[0]
    if not login_state.log_state():
        return redirect('/')

    screennum = 1

    title_dashboard = 'Smarcity'
    subtitle = "Sensor " + name[-2:]
    permission = login_state.current_usergroup

    global selected_sensor

    selected_sensor =  name

    times = []
    dist = []

    result = data_handler.load_data(selected_sensor)

    for k in sorted(result.iterkeys()):
        times.append(k)
        dist.append(result[k])

    # Graph
    title = "Values for " + times[0] + \
            " to " + times[-1]
    bar_chart = pygal.Line(width=1000,
                           height=500,
                           explicit_size=True,
                           title=title,
                           style=DarkSolarizedStyle,
                           disable_xml_declaration=True,
                           y_title='free cm',
                           x_title='Date and time',
                           x_label_rotation=20,
                           x_labels_major_count=10,
                           show_minor_x_labels=False,
                           show_only_major_dots=True)
    bar_chart.x_labels = times
    bar_chart.add(name[-2:], dist)
    # bar_chart.config.force_uri_protocol # Add possible fix to Chrome bug here

    return render_template('start.html', subtitle=subtitle, title=title_dashboard, screennum=screennum,
                           bar_chart=bar_chart, permission=permission, version=version)


@app.route('/getjson.json', methods=['GET', 'POST'])
def getjson():
    global selected_sensor
    result = data_handler.load_data(selected_sensor)
    return jsonify(**result)


# Todo: Move some stuff to own class + make one version with only data from a single sensor
@app.route('/main_graph', methods=['GET', 'POST'])
def main_graph():


    sensors = data_handler.get_sensor_ids()

    colorlist = ['r--', 'bs', 'g^', 'yo', 'rs', 'k^', 'b--']

    plt.figure(figsize=(50,10))

    # red dashes, blue squares and green triangles
    for i in sensors[1:-1]:

        temp = data_handler.load_data(i)

        keylist = []
        for j in temp.keys():
            keylist.append(datetime.datetime.strptime(j, '%Y-%m-%d %H:%M:%S'))

        plt.plot(keylist, temp.values(), colorlist[sensors.index(i)])

    """
    #Work days
    plt.axvspan(datetime.datetime.strptime('2016-05-10 06:00:00', '%Y-%m-%d %H:%M:%S'),
                datetime.datetime.strptime('2016-05-10 13:00:00', '%Y-%m-%d %H:%M:%S'), facecolor='c', alpha=1)
    plt.axvspan(datetime.datetime.strptime('2016-05-11 06:00:00', '%Y-%m-%d %H:%M:%S'),
                datetime.datetime.strptime('2016-05-11 13:00:00', '%Y-%m-%d %H:%M:%S'), facecolor='c', alpha=1)
    plt.axvspan(datetime.datetime.strptime('2016-05-12 06:00:00', '%Y-%m-%d %H:%M:%S'),
                datetime.datetime.strptime('2016-05-12 13:00:00', '%Y-%m-%d %H:%M:%S'), facecolor='c', alpha=1)
    plt.axvspan(datetime.datetime.strptime('2016-05-13 06:00:00', '%Y-%m-%d %H:%M:%S'),
                datetime.datetime.strptime('2016-05-13 13:00:00', '%Y-%m-%d %H:%M:%S'), facecolor='c', alpha=1)
    plt.axvspan(datetime.datetime.strptime('2016-05-17 06:00:00', '%Y-%m-%d %H:%M:%S'),
                datetime.datetime.strptime('2016-05-17 13:00:00', '%Y-%m-%d %H:%M:%S'), facecolor='c', alpha=1)
    plt.axvspan(datetime.datetime.strptime('2016-05-18 06:00:00', '%Y-%m-%d %H:%M:%S'),
                datetime.datetime.strptime('2016-05-18 13:00:00', '%Y-%m-%d %H:%M:%S'), facecolor='c', alpha=1)
    plt.axvspan(datetime.datetime.strptime('2016-05-19 06:00:00', '%Y-%m-%d %H:%M:%S'),
                datetime.datetime.strptime('2016-05-19 13:00:00', '%Y-%m-%d %H:%M:%S'), facecolor='c', alpha=1)
    plt.axvspan(datetime.datetime.strptime('2016-05-20 06:00:00', '%Y-%m-%d %H:%M:%S'),
                datetime.datetime.strptime('2016-05-20 13:00:00', '%Y-%m-%d %H:%M:%S'), facecolor='c', alpha=1)
    plt.axvspan(datetime.datetime.strptime('2016-05-23 06:00:00', '%Y-%m-%d %H:%M:%S'),
                datetime.datetime.strptime('2016-05-23 13:00:00', '%Y-%m-%d %H:%M:%S'), facecolor='c', alpha=1)
    plt.axvspan(datetime.datetime.strptime('2016-05-24 06:00:00', '%Y-%m-%d %H:%M:%S'),
                datetime.datetime.strptime('2016-05-24 13:00:00', '%Y-%m-%d %H:%M:%S'), facecolor='c', alpha=1)"""

    fig = plt
    img = StringIO.StringIO()
    fig.savefig(img)
    img.seek(0)

    return send_file(img, mimetype='image/png')

# Todo: Move some stuff to own class
@app.route('/map_simple.png', methods=['GET', 'POST'])
def map_simple():
    background = data_handler.generate_map()
    img_io = StringIO.StringIO()
    background.save(img_io, 'PNG', quality=70)
    img_io.seek(0)
    try:
        return send_file(img_io, mimetype='image/png')
    except:
        abort(404)

port = os.getenv('PORT', '5000')
if __name__ == "__main__":
    app.secret_key = '60812477'
    #  app.config['SESSION_TYPE'] = 'filesystem'

    '''Debugging. Add/remove after need'''
    #app.debug = True

    '''comment this out for bluemix'''
    #app.run()

    '''comment this out for running locally'''
    app.run(host='0.0.0.0', port=int(port))
