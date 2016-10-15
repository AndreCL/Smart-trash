# -*- coding: utf-8 -*-
"""All in relation with loading the data and the DBs"""
import requests
import json
from operator import itemgetter
import datetime
import time
import re
from cloudant.account import Cloudant
from cloudant.document import Document
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import StringIO
from flask import send_file


class Datahandler:
    """This class handles all the connections to the REST API, the DB (except for login)"""

    def __init__(self):
        self.sensors = ['02014100', '02014101', '02014102', '02014103', '02014104', '02014105']#,
        # '02014106', '02014107', '02014108', '02014109']  # Used to load the sensor data from the database
        self.all_data = {}
        self.latest_data = []

        # Connect to database
        USERNAME = "" # ADD YOUR OWN
        PASSWORD = "" # ADD YOUR OWN
        URL="" #ADD YOUR OWN
        self.client = Cloudant(USERNAME, PASSWORD, url=URL)
        self.client.connect()

    def save_new_data_old(self):
        """Save the data from the HTTP Api"""

        for j in self.sensors:

            temp_sens = []
            counter_updated = 0

            # connect to TTN db
            url = 'http://thethingsnetwork.org/api/v0.1/nodes/' + j + '/?format=json'
            page = requests.get(url)
            page.encoding = 'utf-8'

            if page.text != 'None' and page.text != 'null': # if HTTP Api not down

                unsaved_data = json.loads(page.text)

                # connect to smarcity db
                temp_string = 's' + j
                get_db = self.client[temp_string]
                # if user in self.users:
                data_found = Document(get_db, "raw_data")
                # If sensor in DB, get whats in it
                if data_found.exists():
                    with Document(get_db, "raw_data") as document:
                        saved_data = document['data']

                    # get last time saved on Cloudant DB
                    try:
                        d2 = datetime.datetime.strptime(saved_data[0][u'time'], "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError:
                        try:
                            d2 = datetime.datetime.strptime(saved_data[0][u'time'], "%Y-%m-%dT%H:%M:%SZ")  # Happens when seconds has no decimals
                        except ValueError:
                            d2 = datetime.datetime.strptime(saved_data[0][u'time'][0:25] + "Z", "%Y-%m-%dT%H:%M:%S.%fZ")  # Happens when microseconds have over 25 decimals
                    t2 = time.mktime(d2.timetuple()) + d2.microsecond / 1E6

                    for i in range(len(unsaved_data)):

                        # clean times
                        # clean date measurement
                        # 2016-03-01T12:42:04.285Z
                        try:
                            d1 = datetime.datetime.strptime(unsaved_data[i][u'time'], "%Y-%m-%dT%H:%M:%S.%fZ")
                        except ValueError:
                            try:
                                d1 = datetime.datetime.strptime(unsaved_data[i][u'time'], "%Y-%m-%dT%H:%M:%SZ")  # Happens when seconds has no decimals
                            except ValueError:
                                d1 = datetime.datetime.strptime(saved_data[i][u'time'][0:25] + "Z", "%Y-%m-%dT%H:%M:%S.%fZ")  # Happens when microseconds have over 25 decimals
                        t1 = time.mktime(d1.timetuple()) + d1.microsecond / 1E6

                        # Unencrypt the data from unsaved data
                        unencrypt = unsaved_data[i]
                        unencrypt[u'data'] = unencrypt[u'data'].decode('base64')

                        if t1 <= t2:
                            break
                        elif t1 > t2:
                            temp_sens.append(unencrypt) # To save raw, replace unencrypt with unsaved_data[i]
                            counter_updated += 1

                with Document(get_db, "raw_data") as document:
                        document['data'] = temp_sens + saved_data
                        document.save()

            # print "Database updated. Added " + str(counter_updated) + " elements to " + j #debugging

        print "Done updating HTTP"

    def save_new_data(self):
        """Save the data from the MQTT Api"""

        for j in self.sensors:

            temp_sens = []
            unsaved_processed = []

            # connect to TTN db
            url = 'http://bluemixmqtt.eu-gb.mybluemix.net/' + j
            page = requests.get(url)
            page.encoding = 'utf-8'
            unsaved_data = json.loads(page.text)

            #Process the data before saving
            for i in range(len(unsaved_data)):

                temp_dict = {}

                temp = json.loads(unsaved_data[i]['payload'])

                temp_dict["rssi"]= temp['metadata'][0][u'rssi']
                temp_dict["gateway_eui"]= temp['metadata'][0][u'gateway_eui']
                temp_dict["datarate"]= temp['metadata'][0][u'datarate']
                temp_dict["time"]= temp['metadata'][0][u'gateway_time'] # Replace with server_time?
                temp_dict["data"]= temp['payload']
                temp_dict["frequency"]= temp['metadata'][0][u'frequency']
                temp_dict["node_eui"]= j

                unsaved_processed.append(temp_dict)

            newlist = sorted(unsaved_processed, key=itemgetter('time'), reverse=True)

            # connect to smarcity db
            temp_string = 's' + j
            get_db = self.client[temp_string]
            # if user in self.users:
            data_found = Document(get_db, "raw_data")
            # If sensor in DB, get whats in it
            if data_found.exists():
                with Document(get_db, "raw_data") as document:
                    saved_data = document['data']

                counter_updated = 0

                # get last time saved on Cloudant DB
                try:
                    d2 = datetime.datetime.strptime(saved_data[0][u'time'], "%Y-%m-%dT%H:%M:%S.%fZ")
                except ValueError:
                    try:
                        d2 = datetime.datetime.strptime(saved_data[0][u'time'], "%Y-%m-%dT%H:%M:%SZ")  # Happens when seconds has no decimals
                    except ValueError:
                        d2 = datetime.datetime.strptime(saved_data[0][u'time'][0:25] + "Z", "%Y-%m-%dT%H:%M:%S.%fZ")  # Happens when microseconds have over 25 decimals
                t2 = time.mktime(d2.timetuple()) + d2.microsecond / 1E6

                for i in range(len(newlist)): #replace with new thing

                    # clean times
                    # clean date measurement
                    # 2016-03-01T12:42:04.285Z
                    try:
                        d1 = datetime.datetime.strptime(newlist[i][u'time'], "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError:
                        try:
                            d1 = datetime.datetime.strptime(newlist[i][u'time'], "%Y-%m-%dT%H:%M:%SZ")  # Happens when seconds has no decimals
                        except ValueError:
                            d1 = datetime.datetime.strptime(newlist[i][u'time'][0:25] + "Z", "%Y-%m-%dT%H:%M:%S.%fZ")  # Happens when microseconds have over 25 decimals
                    t1 = time.mktime(d1.timetuple()) + d1.microsecond / 1E6

                    # Unencrypt the data from unsaved data
                    unencrypt = newlist[i]
                    unencrypt[u'data'] = unencrypt[u'data'].decode('base64')

                    if t1 <= t2:
                        break
                    elif t1 > t2:
                        temp_sens.append(unencrypt) # To save raw, replace unencrypt with unsaved_data[i]
                        counter_updated += 1

            with Document(get_db, "raw_data") as document:
                    document['data'] = temp_sens + saved_data
                    document.save()

            # print "Database updated. Added " + str(counter_updated) + " elements to " + j #debugging

        print "Done updating MQTT"

    def get_sensor_ids(self):
        """Returns the sensor ids"""
        return self.sensors

    def load_all_data(self, mode_req):
        """
        :param mode_req: 1=Returns html ready tbody (table body)
        2=Returns a list of lists with all the sensor data (date, measurement, sensor_id) in order of time
        """
        temp = []
        self.all_data = {}

        # related db called u's02014100' and so on
        for j in self.sensors:
            # extract data from that one
            temp_string = 's' + j
            get_db = self.client[temp_string]

            data_found = Document(get_db, "raw_data")

            # If sensor in DB, get whats in it
            if data_found.exists():
                with Document(get_db, "raw_data") as document:
                    data = document['data']

                    if data: # if not empty

                        for i in range(len(data)):

                            # clean date measurement
                            # 2016-03-01T12:42:04.285Z
                            try:
                                d = datetime.datetime.strptime(data[i][u'time'], "%Y-%m-%dT%H:%M:%S.%fZ")
                            except ValueError:
                                try:
                                    d = datetime.datetime.strptime(data[i][u'time'], "%Y-%m-%dT%H:%M:%SZ")  # Happens when seconds has no decimals
                                except ValueError:
                                    d = datetime.datetime.strptime(data[i][u'time'][0:25] + "Z", "%Y-%m-%dT%H:%M:%S.%fZ")  # Happens when microseconds have over 25 decimals
                            t = time.mktime(d.timetuple()) + d.microsecond / 1E6
                            r = re.sub('[^0-9]', '', data[i][u'data']) # Changed from data_plain due to HTTP Api update
                            if r == '':
                                r = re.sub('[^0-9]', '', data[i][u'data_plain'])

                            temp.append([time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(t))), int(r), j])

        ordered_temp = sorted(temp, key=itemgetter(0), reverse=True)
        self.all_data = ordered_temp

        if mode_req==1:
            for_html = "<div class=\"table-responsive\" style=\"height: 250px; overflow-y: scroll;\"> <table class=\"table table-striped\"> <thead> <tr> "
            for_html += "<th>Time</th> <th>Sensor</th> <th>Data</th> </tr> </thead><tbody>"
            for i in ordered_temp:
                for_html += "<tr> <td>" + str(i[0]) + "</td> <td>" + str(i[2][-2:]) + "</td> <td> " + str(i[1]) + "</td> </tr>"
            for_html += "</tbody> </table> </div>"
            return for_html
        elif mode_req==2:
            return ordered_temp

    def load_latest_data(self, mode_ret):
        """:param mode_ret: 1=Returns HTML code ready to display in the main screen of dashboard
         2=Returns a dictionary of all the latest data from each sensor"""
        self.latest_data = [] # Not implemented
        latest = []

        time_now = datetime.datetime.now()

        display_it = "<div class=\"row placeholders\">"
        # related db called u's02014100' and so on
        for j in self.sensors:
            # extract data from that one
            temp_string = 's' + j
            get_db = self.client[temp_string]

            data_found = Document(get_db, "raw_data")

            # If sensor in DB, get whats in it
            if data_found.exists():
                with Document(get_db, "raw_data") as document:
                    data = document['data']

                    if data: # if not empty
                        #clean date measurement
                        # 2016-03-01T12:42:04.285Z
                        try:
                            d = datetime.datetime.strptime(data[0][u'time'], "%Y-%m-%dT%H:%M:%S.%fZ")
                        except ValueError:
                            try:
                                d = datetime.datetime.strptime(data[0][u'time'], "%Y-%m-%dT%H:%M:%SZ")  # Happens when seconds has no decimals
                            except ValueError:
                                d = datetime.datetime.strptime(data[0][u'time'][0:25] + "Z", "%Y-%m-%dT%H:%M:%S.%fZ")  # Happens when microseconds have over 25 decimals
                        t = time.mktime(d.timetuple()) + d.microsecond / 1E6
                        r = re.sub('[^0-9]', '', data[0][u'data'])  # Changed from data_plain due to HTTP Api update
                        if r == '':
                                r = re.sub('[^0-9]', '', data[0][u'data_plain'])

                        # Changing to make it simpler here
                        temp_r = abs(int(r) - 100)
                        temp_time = (time_now - datetime.datetime.fromtimestamp(float(t) ))
                        if temp_time.days > 0:
                            temp_2_time = str(temp_time.days) + "d ago"
                        elif temp_time.seconds >= 3600:
                            temp_2_time = str(int(temp_time.seconds / 3600)) + "h ago"
                        elif temp_time.seconds >= 60:
                            temp_2_time = str(int(temp_time.seconds / 60)) + "m ago"
                        else:
                            temp_2_time = str(int(temp_time.seconds)) + "s ago"
                        latest.append([j[-2:], temp_r, temp_2_time])

                        display_it += " <div class=\"col-xs-6 col-sm-3 placeholder\"> <a href=\"/sensor/" + j + "\">"
                        display_it += "<img src=\"/static/images/bin_default.jpg\" width=\"200\" height=\"200\" class=\"img-responsive\" alt=\"Generic placeholder thumbnail\">"
                        display_it += "<h4>Node: " + j[-2:] + "</h4>" + "<span class=\"text-muted\"> "
                        display_it += r + "cm free at " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(t))) + "</span> </a> </div>"

        display_it += " </div>"

        if mode_ret==1:
            return display_it
        elif mode_ret==2:
            return latest

    def load_data(self, sensor_id):
        """Returns dict of individual sensor data"""
        temp = {}

        temp_string = 's' + str(sensor_id)
        get_db = self.client[temp_string]

        data_found = Document(get_db, "raw_data")

        # If sensor in DB, get whats in it
        if data_found.exists():
            with Document(get_db, "raw_data") as document:
                data = document['data']

                if data: # if not empty

                    for i in range(len(data)):

                        #clean date measurement
                        # 2016-03-01T12:42:04.285Z
                        try:
                            d = datetime.datetime.strptime(data[i][u'time'], "%Y-%m-%dT%H:%M:%S.%fZ")
                        except ValueError:
                            try:
                                d = datetime.datetime.strptime(data[i][u'time'], "%Y-%m-%dT%H:%M:%SZ")  # Happens when seconds has no decimals
                            except ValueError:
                                d = datetime.datetime.strptime(data[i][u'time'][0:25] + "Z", "%Y-%m-%dT%H:%M:%S.%fZ")  # Happens when microseconds have over 25 decimals
                        t = time.mktime(d.timetuple()) + d.microsecond / 1E6
                        r = re.sub('[^0-9]', '', data[i][u'data']) # Changed from data_plain due to HTTP Api update
                        if r == '':
                                r = re.sub('[^0-9]', '', data[i][u'data_plain'])

                        temp[time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(t)))] = int(r)

        return temp

    def gettime(self):
        """Returns time as datetime"""
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        return st


    def get_temp_data_latest(self):
        """Returns latest weather conditions"""
        # connect to weather HTTP
        url = "" # ADD YOUR OWN
        page = requests.get(url)
        page.encoding = 'utf-8'

        if page.text != 'None' and page.text != 'null': # if HTTP Api not down

            unsaved_data = json.loads(page.text)

            #print unsaved_data

            icon ="/static/images/weathericons/icon" + str(unsaved_data['observation']['icon_code']) + ".png"

            desc_icon = unsaved_data['observation']['phrase_32char']

            temperature = str(unsaved_data['observation']['metric']['temp']) + "°C"

            humidity = str(unsaved_data['observation']['metric']['rh']) + "%"

            wind_direction_cardinal = unsaved_data['observation']['wdir_cardinal']

            wind_speed = str(unsaved_data['observation']['metric']['wspd']) + "km/h"

        return [icon, desc_icon, temperature, humidity, wind_direction_cardinal, wind_speed]

    def generate_map(self):
        #Get the data
        temperature = self.get_temp_data_latest()
        data = self.load_latest_data(2)

        """Create the map"""
        #Map in background
        background = Image.open("static/images/map.png").convert("RGBA") #Size: 1253x994

        #Add weather stuff
        icon= Image.open(temperature[0][1:]).convert("RGBA") #Size: 200x200
        desc_icon = temperature[1]
        temperature = temperature[2].decode("utf8")
        humidity = temperature[3]

        background.paste(icon, (0, 794), icon)

        #font = ImageFont.truetype("ariblk.ttf", 16)
        font = ImageFont.truetype(font="static/fonts/ariblk.ttf" , size=16)
        draw = ImageDraw.Draw(background)
        draw.text((80, 874),temperature,(0,0,0),font=font)
        #font = ImageFont.truetype("ariblk.ttf", 14)
        font = ImageFont.truetype(font="static/fonts/ariblk.ttf" ,size=14)
        draw = ImageDraw.Draw(background)
        draw.text((100-(len(desc_icon)*4), 894),desc_icon,(0,0,0),font=font)

        #Add bin info
        positions = [(50, 300), (600, 400), (300,600), (550, 600), (650, 550), (750, 550)]
        positions2 = [(55, 320), (605, 420), (305,620), (555, 620), (655, 570), (755, 570)]

        for i in range(len(positions)):
            if data[i][2][-5:] == "d ago":
                bin = Image.open("static/images/bin2_gray.png") #2400x2400
                bin = bin.resize((100,100))
                background.paste(bin, positions[i], bin)
                #font = ImageFont.truetype("ariblk.ttf", 40)
                font = ImageFont.truetype(font="static/fonts/ariblk.ttf" ,size=40)
                draw = ImageDraw.Draw(background)
                draw.text(positions2[i],"???",(0,0,0),font=font) #comment for non-questionmark version, replace next line with if data[i][1] < 50:

            elif data[i][1] < 50:
                bin = Image.open("static/images/bin2_green.png") #2400x2400
                bin = bin.resize((100,100))
                background.paste(bin, positions[i], bin)
                #font = ImageFont.truetype("ariblk.ttf", 40)
                font = ImageFont.truetype(font="static/fonts/ariblk.ttf" ,size=40)
                draw = ImageDraw.Draw(background)
                draw.text(positions2[i],str(data[i][1])+"%",(0,0,0),font=font)
            elif data[i][1] < 75:
                bin = Image.open("static/images/bin2_yellow.png") #2400x2400
                bin = bin.resize((100,100))
                background.paste(bin, positions[i], bin)
                #font = ImageFont.truetype("ariblk.ttf", 40)
                font = ImageFont.truetype(font="static/fonts/ariblk.ttf" ,size=40)
                draw = ImageDraw.Draw(background)
                draw.text(positions2[i],str(data[i][1])+"%",(0,0,0),font=font)
            else:
                bin = Image.open("static/images/bin2_red.png") #2400x2400
                bin = bin.resize((100,100))
                background.paste(bin, positions[i], bin)
                #font = ImageFont.truetype("ariblk.ttf", 38)
                font = ImageFont.truetype(font="static/fonts/ariblk.ttf" ,size=38)
                draw = ImageDraw.Draw(background)
                draw.text(positions2[i],str(data[i][1])+"%",(0,0,0),font=font)

        return background



