# Forked from https://github.com/mowbraym/Brewfather_iSpindel
# Original Comments below

# brewfather craftbeerpi3 plugin
# Log iSpindel temperature, SG and Battery data from CraftBeerPi 3.0 to the brewfather app
# https://brewfather.app/
#
# Note this code is heavily based on the Thingspeak plugin by Atle Ravndal
# and I acknowledge his efforts have made the creation of this plugin possible
# It is also now heavily based on the BrewStat.us and Brewfather modules I've written
#
from modules import cbpi
from thread import start_new_thread
import logging
import requests
import datetime
import json

DEBUG = False
drop_first = None

# Parameters
brewfather_iSpindel_id = None

def log(s):
    if DEBUG:
        s = "brewfather_iSpindel: " + s
        cbpi.app.logger.info(s)

@cbpi.initalizer(order=9000)
def init(cbpi):
    cbpi.app.logger.info("brewfather_iSpindel plugin Initialize")
    log("Brewfather_iSpindel params")
# the unique id value (the bit following id= in the "Cloud URL" in the setting screen
    global brewfather_iSpindel_id

    brewfather_iSpindel_id = cbpi.get_config_parameter("brewfather_iSpindel_id", None)
    log("Brewfather brewfather_iSpindel_id %s" % brewfather_iSpindel_id)

    if brewfather_iSpindel_id is None:
        log("Init brewfather_iSpindel config URL")
        try:
# TODO: is param2 a default value?
            cbpi.add_config_parameter("brewfather_iSpindel_id", "", "text", "Brewfather_iSpindel id")
        except:
            cbpi.notify("Brewfather_iSpindel Error", "Unable to update Brewfather_iSpindel id parameter", type="danger")
    log("Brewfather_iSpindel params ends")

# interval=900 is 900 seconds, 15 minutes, same as the Tilt Android App logs.
# if you try to reduce this, brewfather will throw "ignored" status back at you
@cbpi.backgroundtask(key="brewfather_iSpindel_task", interval=900)
def brewfather_iSpindel_background_task(api):
    log("brewfather_iSpindel background task")
    global drop_first
    if drop_first is None:
        drop_first = False
        return False

    if brewfather_iSpindel_id is None:
        return False

    payload = {}
    for key, value in cbpi.cache.get("sensors").iteritems():
        try:
            log("value.name %s value.instance.last_value %s value.type %s" % (value.name, value.instance.last_value, value.type))

            if (value.type == "iSpindel"):
                payload['name'] = value.instance.key
                if (value.instance.sensorType == "Temperature"):
                    payload['temperature'] = value.instance.last_value
                if (value.instance.sensorType == "RSSI"):
                    payload['RSSI'] = value.instance.last_value
                if (value.instance.sensorType == "Battery"):
                    payload['battery'] = value.instance.last_value
                if (value.instance.sensorType == "Gravity"):
                    payload['gravity'] = value.instance.last_value
                if (value.instance.sensorType == 'Angle'):
                    payload['angle'] = value.instance.last_value

        except BaseException as error:
            cbpi.notify("Brewfather iSpindel Error", "Unable to collect sensor data. " + str(error), type="danger", timeout=None)
            log("Unable to collect sensor data. " + str(error))

    ispindel_id = cbpi.get_config_parameter("brewfather_iSpindel_id", None)
    url = "http://log.brewfather.net/ispindel"
    headers = {
        'Content-Type': "application/json",
        'Cache-Control': "no-cache"
    }

    querystring = {"id":str(ispindel_id)}
    log("Payload %s querystring %s" % (json.dumps(payload), querystring))
    #cbpi.notify("Brewfather iSpindel Payload", "Payload %s querystring %s" % (json.dumps(payload), querystring), type="success", timeout=None)
    response = requests.request("POST", url, json=payload, headers=headers, params=querystring)
    if response.status_code != 200:
        cbpi.notify("Brewfather iSpindel Error", "Received unsuccessful response. Ensure API ID is correct. HTTP Error Code: " + str(response.status_code), type="danger", timeout=None)
    if response.status_code == 200:
        response_content = json.loads(response.text)
        if response_content['result'] != "success":
            cbpi.notify("Brewfather iSpindel Notification", "POST Unsuccsessful. Result: %s" % response_content['result'], type="danger", timeout=None)

    log("Result %s" % response.text)
    log("brewfather_iSpindel done")
