
from gevent import monkey
monkey.patch_all()
from flask import Flask, request, render_template, make_response
import argparse
from gevent import pywsgi
import os
import requests
import openai
import json

import random
from flask_cors import CORS, cross_origin
from logger import sys_logger, info_external_request, info_external_response
from statistics import make_statistics
import datetime



class ExecuteParameter:
    def __init__(self):
        self.start_date = datetime.datetime.strptime("20230120 00:00:00", "%Y%m%d %H:%M:%S")
        self.end_date = datetime.datetime.now()

    def set_start_date(self, _start_date_str):
        if _start_date_str is None:
            return
        self.start_date = datetime.datetime.strptime("%s 00:00:00" % _start_date_str, "%Y%m%d %H:%M:%S")

    def set_end_date(self, _end_date_str):
        if _end_date_str is None:
            return
        self.end_date = datetime.datetime.strptime("%s 23:59:59" % _end_date_str, "%Y%m%d %H:%M:%S")


def start_sever():
    print("Starting lgo server ... ")
    app = Flask(__name__)
    # CORS(app, resources=r'/*', supports_credentials=True, methods=['GET', 'POST', 'OPTIONS'])

    _http_id = "0.0.0.0"
    _port = 8080

    @app.route('/get_stats', methods=['GET'])
    # @cross_origin(supports_credentials=True)
    def response_get_stats():
        _response = None
        if request.method == 'GET':
            _start_date = request.args.get("startdate")
            _end_date = request.args.get("enddate")
            
            _execute_parameter = ExecuteParameter()
            _execute_parameter.set_start_date(_start_date)
            _execute_parameter.set_end_date(_end_date)

            _stats_str = make_statistics(_execute_parameter)
            print(_stats_str)
            return render_template("index_stats.html", content=_stats_str)
        return render_template("index_stats.html", content="Failed to get statistics!")

    server = pywsgi.WSGIServer((_http_id, _port), app)
    print("Listening, ipaddr: %s, port: %d" % (_http_id, _port))
    server.serve_forever()
    print("Stop listening!")


if __name__ == '__main__':
    
    start_sever()

