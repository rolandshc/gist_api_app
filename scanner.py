import requests
import time
import logging
import json
import datetime
import config
import csv
import pytz
import os

def getDateTimeNow():
    return datetime.datetime.now(pytz.utc).strftime('%d/%m/%Y, %H:%M:%S')

def getUsers():
    try:
        results = []
        with open(config.csvFilePath["users"], newline='') as inputfile:
            for row in csv.reader(inputfile):
                results.append(row[0])
    except Exception as e:
        logging.warning('{0} : failed to read user list from file. error: {1}'.format(getDateTimeNow(),e))
    logging.info('{0} : Scanned users -{1}'.format(getDateTimeNow(),results))
    return results

def getGist(user):
    url = 'https://api.github.com/users/{0}/gists'.format(user)
    resp = requests.get(url=url)
    data = resp.json()
    gists = []
    currentDateTime = datetime.datetime.now(pytz.utc)
    date = currentDateTime - datetime.timedelta(days=config.period['days'],hours=config.period['hours'], seconds= config.period['seconds'])  
    try:
        for i in range(len(data)):
            dateTimeStr = data[i]['updated_at']
            updatedAt = datetime.datetime.strptime(dateTimeStr, '%Y-%m-%dT%H:%M:%SZ')
            updatedAt_local = pytz.utc.localize(updatedAt)
            if updatedAt_local >= date:
                gists.append(data[i])
    except Exception as e:
        logging.warning('{0} : Github-API: Failed to get gist through github-API'.format(getDateTimeNow()))
        if e:
            logging.warning('{0} : Error message: {1}'.format(getDateTimeNow(), e))
        if len(data['message']) != 0:
            logging.warning('{0} : Response message: {1}'.format(getDateTimeNow(),data['message']))

    return gists
def formatGist(gists):
    formatted_gists = []
    for i in range(len(gists)):
        gistDict = {
            "user": gists[i]['owner']['login'],
        "html_url": gists[i]['html_url'],
        "update_date": gists[i]['updated_at']
        }
        formatted_gists.append(gistDict)
    return formatted_gists

def writeGist(formatted_gists):
    try:
        out_file = open("gists.txt", "a")
        out_file.write(json.dumps(formatted_gists, indent=4) + "\n")
        out_file.close()
    except Exception as e:
        logging.warning('{0} : failed to write gist to file. error: {1}'.format(getDateTimeNow(),e))

def createActivity(gists):
    try:
        activityId = []
        for i in range(len(gists)):
            dateTimeStr = gists[i]['updated_at']
            updatedAt = datetime.datetime.strptime(dateTimeStr, '%Y-%m-%dT%H:%M:%SZ')
            tz = pytz.timezone(config.period['timezone'])
            updatedAt_local = tz.localize(updatedAt)
            due_date = datetime.datetime.now(pytz.utc).strftime('%Y-%m-%d')
            due_time = datetime.datetime.now(pytz.utc).strftime('%I:%M %p')
            url = "https://{0}.pipedrive.com/api/v1/activities?api_token={1}".format(config.pipedrive['domain'],config.pipedrive['api-key'])
            data = {
                "subject": "Gist created - User: {0} at {1}".format(gists[i]['owner']['login'],str(updatedAt_local)),
                "type": "Task",
                "note":  "gist url: " + gists[i]['html_url'],
                "due_date": due_date,
                "due_time": due_time
            }
            resp = requests.post(url, json=data)
            response = resp.json()
            if response['data']['id']:
                activityId.append(response['data']['id'])
            else:
                logging.warning('{0} : Pipedrive-API: failed to add activity to pipedrive. Response: {1}'.format(getDateTimeNow(),resp))
    except Exception as e:
        logging.warning('{0} : Pipedrive-API: failed to add activity to pipedrive. Error: {1}'.format(getDateTimeNow(),e))
    logging.info('{0} : Pipedrive-API: Created activities successfully for id : {1}'.format(getDateTimeNow(), str(activityId)))

def scan():
    #logging.basicConfig(filename='system.log', level=logging.DEBUG)
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
    users = getUsers()
    open('gists.txt', 'w').close()
    logging.info('{0} : Start Scanning'.format(getDateTimeNow()))
    for i in range(len(users)):
        gists = getGist(users[i])
        formatted_gists = formatGist(gists)
        if len(gists)>0:
            logging.info('{0} : {1} new gists created by user {2} were found.'.format(getDateTimeNow(),str(len(gists)),str(users[i])))
            writeGist(formatted_gists)
            createActivity(gists)
        else:
            logging.info('{0} : NO new gist created by user {1} was found.'.format(getDateTimeNow(),str(users[i])))
    logging.info('{0} : Completed Scanning'.format(getDateTimeNow()))

