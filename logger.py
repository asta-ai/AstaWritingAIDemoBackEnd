import os
import sys
import logging
import datetime
import json


class SystemLogger:

    def __init__(self, _logger_name=__name__,  _log_dir=r"./log"):

        self.logger = None
        self.logger_name = _logger_name
        self.log_dir = _log_dir

        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        self.initialize(_logger_name)

    def initialize(self, _logger_name):

        # initialize logger config
        _format = '[%(asctime)s][%(name)s][%(levelname)s]: %(message)s'
        logging.basicConfig(level=logging.INFO, format=_format)

        # get logger
        self.logger = logging.getLogger(_logger_name)

        self.logger.setLevel(logging.INFO)

        # get file name
        _log_path_name = self.get_log_path_name()

        #
        _file_handler = logging.FileHandler(_log_path_name)

        _file_handler.setLevel(logging.INFO)

        _formatter = logging.Formatter(_format)

        _file_handler.setFormatter(_formatter)

        self.logger.addHandler(_file_handler)

        return self.logger

    def set_level(self, _level):
        self.logger.set_level(_level)

    def get_log_path_name(self):
        _now = datetime.datetime.now()
        _file_name = "%s.log" % _now.strftime("%Y_%m_%d_%H_%M_%S")
        _file_path_name = os.path.join(self.log_dir, _file_name)
        return _file_path_name

    def info(self, _msg):
        self.logger.info(_msg)

    def debug(self, _msg):
        self.logger.debug(_msg)

    def warning(self, _msg):
        self.logger.warning(_msg)


sys_logger = SystemLogger()


def info_external_request(_request, _tag="UNKNOWN", _ignore_fields_in_body=None):

    _raw_request_str = "%s" % _request.__dict__

    _headers_json_str = "{}"
    try:
        _headers = {_name: _value for _name, _value in list(_request.headers)}
        _headers_json_str = json.dumps(_headers, ensure_ascii=False).strip()
    except Exception as e:
        _headers_json_str = "{}"

    _body_json_str = "{}"
    try:
        _body_dict = _request.get_data()
        if _body_dict is not None:
            if _ignore_fields_in_body is not None:
                for _field_name in _ignore_fields_in_body:
                    if _field_name in _body_dict.keys():
                        _body_dict[_field_name] = "<IGNORE>"
            _body_json_str = _body_dict.decode(encoding='utf-8').strip()
    except:
        _body_json_str = "{}"

    _dict = {
        "method": _request.method,
        "headers": _headers_json_str,
        "body": _body_json_str,
        "raw": _raw_request_str
    }
    
    _json = json.dumps(_dict, ensure_ascii=False).strip()
    sys_logger.info("[REQUEST][%s]: %s" % (_tag, _json))


def info_external_response(_response, _tag="UNKNOWN"):

    _raw_response_str = "%s" % _response.__dict__

    _headers_json_str = "{}"
    try:
        _headers = {_name: _value for _name, _value in list(_response.headers)}
        _headers_json_str = json.dumps(_headers, ensure_ascii=False).strip()
    except Exception as e:
        _headers_json_str = "{}"

    _body_json_str = "{}"
    try:
        _data = _response.get_data()
        if _data is not None:
            _body_json_str = _data.decode(encoding='utf-8').strip()
    except:
        _body_json_str = "{}"

    _dict = {
        "headers": _headers_json_str,
        "body": _body_json_str,
        "raw": _raw_response_str
    }
    
    _json = json.dumps(_dict, ensure_ascii=False).strip()
    sys_logger.info("[RESPONSE][%s]: %s" % (_tag, _json))