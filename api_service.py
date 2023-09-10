
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

from internal_request import InternalRequestHeader, InternalRequestBody, InternalRequest
from internal_response import MockedInternalCompletionResponse, InternalSuggCMDResponse
from internal_response import InternalTelementryResponse, InternalCompletionResponse, InternalOptionsResponse, InternalErrorResponse
import uuid


def assgin_raw_id_to_request(_request):
    _request.headers = list(_request.headers)
    _request.headers.append(["RawId", "%s" % uuid.uuid1()])


def start_sever():
    print("Starting server ... ")
    app = Flask(__name__)
    # CORS(app, resources=r'/*', supports_credentials=True, methods=['GET', 'POST', 'OPTIONS'])

    _http_id = "0.0.0.0"
    _port = 8888

    @app.route('/api/report_telementry', methods=['GET', 'POST', 'OPTIONS'])
    # @cross_origin(supports_credentials=True)
    def response_report_telementry():

        assgin_raw_id_to_request(request)

        info_external_request(request, "TELEMENTRY")

        _response = None
        if request.method == 'POST':
            _internal_request = InternalRequest.create_request(request)
            _internal_response = InternalTelementryResponse(_internal_request=_internal_request)
            _response = _internal_response.get_response()

        elif request.method == "OPTIONS":
            _internal_response = InternalTelementryResponse(_internal_request=None)
            _response = _internal_response.get_response()
        else:
            _internal_response = InternalErrorResponse("Failed! Don't support request method: %s" % request.method)
            _response = _internal_response.get_response()

        info_external_response(_response, "TELEMENTRY")

        return _response

    @app.route('/api/get_response', methods=['GET', 'POST', 'OPTIONS'])
    # @cross_origin(supports_credentials=True)
    def response_get_response():
        
        assgin_raw_id_to_request(request)

        info_external_request(request, "GET_RESPONSE")

        _response = None
        if request.method == 'POST':
            _internal_request = InternalRequest.create_request(request)
            _internal_response = InternalCompletionResponse(_internal_request)
            _response = _internal_response.get_response()

        elif request.method == "OPTIONS":
            _internal_response = InternalOptionsResponse(None)
            _response = _internal_response.get_response()
        else:
            _internal_response = InternalErrorResponse("Failed! Don't support request method: %s" % request.method)
            _response = _internal_response.get_response()

        info_external_response(_response, "GET_RESPONSE")

        return _response

    @app.route('/api/suggest_commands', methods=['GET', 'POST', 'OPTIONS'])
    # @cross_origin(supports_credentials=True)
    def response_suggest_commands():

        assgin_raw_id_to_request(request)

        info_external_request(request, "SUGGEST_COMMANDS")

        _response = None
        if request.method == 'POST':
            _internal_request = InternalRequest.create_request(request)
            _internal_response = InternalSuggCMDResponse(_internal_request)
            _response = _internal_response.get_response()

        elif request.method == "OPTIONS":
            _internal_response = InternalOptionsResponse(None)
            _response = _internal_response.get_response()
        else:
            _internal_response = InternalErrorResponse("Failed! Don't support request method: %s" % request.method)
            _response = _internal_response.get_response()    

        info_external_response(_response, "SUGGEST_COMMANDS")
        
        return _response

    @app.route('/api/debug', methods=['GET', 'POST', 'OPTIONS'])
    # @cross_origin(supports_credentials=True)
    def response_debug():

        _response = None

        if request.method == 'POST':
            _internal_request = InternalRequest.create_request(request)
            _internal_response = InternalSuggCMDResponse(_internal_request)
            _response = _internal_response.get_response()

        elif request.method == "OPTIONS":
            _internal_response = InternalOptionsResponse(_internal_request)
            _response = _internal_response.get_response()
            return _response

        else:
            _internal_response = InternalErrorResponse("Failed! Don't support request method: %s" % request.method)
            _response = _internal_response.get_response()

        return _response


    server = pywsgi.WSGIServer((_http_id, _port), app)
    print("Listening, ipaddr: %s, port: %d" % (_http_id, _port))
    server.serve_forever()
    print("Stop listening!")


if __name__ == '__main__':
    
    start_sever()

