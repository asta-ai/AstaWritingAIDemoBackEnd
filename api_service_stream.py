import base64
import time
from datetime import datetime

from gevent import monkey
monkey.patch_all()
from flask import Flask, request, render_template, make_response, Response
import argparse
from gevent import pywsgi
import os
import requests
import json

import random
from flask_cors import CORS, cross_origin
from logger import sys_logger, info_external_request, info_external_response

from internal_request import InternalRequestHeader, InternalRequestBody, InternalRequest
from internal_response import MockedInternalCompletionResponse, InternalSuggCMDResponse
from internal_response import InternalStreamCompletionResponse, InternalTelementryResponse, InternalCompletionResponse, InternalOptionsResponse, InternalErrorResponse
from internal_response import InternalParseFileContentResponse
import uuid

import openai
import openai_utils

import urllib

from werkzeug.utils import secure_filename


def assgin_raw_id_to_request(_request):
    _request.headers = list(_request.headers)
    _request.headers.append(["RawId", "%s" % uuid.uuid1()])
    


def start_sever():
    print("Starting server ... ")
    app = Flask(__name__)
   
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
            _internal_response = InternalErrorResponse(_error_code=500, _error_msg="Failed! Don't support request method: %s" % request.method)
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
            _internal_response = InternalErrorResponse(_error_code=500, _error_msg="Failed! Don't support request method: %s" % request.method)
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
            _internal_response = InternalErrorResponse(_error_code=500, _error_msg="Failed! Don't support request method: %s" % request.method)
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

    @app.route('/get_response_stream')
    def progress():

        assgin_raw_id_to_request(request)
        info_external_request(request, "GET_RESPONSE_STREAM")

        if "params" not in request.args.keys():
            _error_msg = "Failed! \"params\" is not existing in request!"
            sys_logger.info(_error_msg)
            _internal_response = InternalErrorResponse(_error_code=500, _error_msg=_error_msg)
            _response = _internal_response.get_response()

            info_external_response(_response, "GET_RESPONSE_STREAM")
            return _response

        # get params
        _base64_str = request.args.get("params")
        _body = base64.b64decode(_base64_str).decode("utf-8")
        _body = urllib.parse.unquote(_body, encoding="utf-8")

        _internal_request = InternalRequest.create_request(request, _body)
        _internal_response = InternalStreamCompletionResponse(_internal_request)
        _response = _internal_response.get_response()

        return _response

    @app.route('/api/parse_file_content', methods=['GET', 'POST', 'OPTIONS'])
    def parse_file_content():

        assgin_raw_id_to_request(request)

        info_external_request(request, "PARSE_FILE_CONTENT", _ignore_fields_in_body=["Base64_Content"])

        if request.method == 'POST':
            _internal_request = InternalRequest.create_request(request)
            _internal_response = InternalParseFileContentResponse(_internal_request)
            _response = _internal_response.get_response()
        elif request.method == "OPTIONS":
            _internal_response = InternalOptionsResponse(None)
            _response = _internal_response.get_response()
        else:
            _internal_response = InternalErrorResponse(_error_code=500, _error_msg="Failed! Don't support request method: %s" % request.method)
            _response = _internal_response.get_response()

        info_external_response(_response, "PARSE_FILE_CONTENT")
        return _response

    """
    @app.route('/api/get_response_stream', methods=['GET', 'POST', 'OPTIONS'])
    # @cross_origin(supports_credentials=True)
    def response_get_response_stream():

        assgin_raw_id_to_request(request)

        info_external_request(request, "GET_RESPONSE_STREAM")

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

        info_external_response(_response, "GET_RESPONSE_STREAM")

        return _response
    """

    server = pywsgi.WSGIServer((_http_id, _port), app)
    print("Listening, ipaddr: %s, port: %d" % (_http_id, _port))
    server.serve_forever()
    print("Stop listening!")


if __name__ == '__main__':
    
    start_sever()

