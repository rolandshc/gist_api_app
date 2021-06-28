from flask import Flask
from flask_restful import Resource, Api
import pandas as pd
import atexit
from flask_apscheduler import APScheduler
import scanner
import config
import logging
import os
import datetime
app = Flask(__name__)
api = Api(app)
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
sec = config.period['seconds'] + config.period['hours'] * 3600 + config.period['days'] * 3600 * 24
scheduler = APScheduler()
scheduler.add_job(func=scanner.scan, trigger="interval", seconds=sec, id="Schedular", next_run_time=datetime.datetime.now())
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

class Users(Resource):
     def get(self):
        try:
            df = pd.read_csv('users.csv',header=None)
            data = df.to_dict()
            return {'data': data}, 200  # return data and 200 OK code
        except pd.errors.EmptyDataError:
            return ('', 204)

class Gists(Resource):
     def get(self):
        try:
            with open('gists.txt') as f:
                lines = f.readlines()
            response = app.response_class(
            response=lines,
            status=200
            )
            return response 
        except pd.errors.EmptyDataError:
            return ('', 204)

    
api.add_resource(Users, '/users')  
api.add_resource(Gists, '/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)  # run our Flask app
