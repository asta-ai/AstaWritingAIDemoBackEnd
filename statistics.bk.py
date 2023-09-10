import os
import re
import sys
import glob
import datetime
import json
from prettytable import PrettyTable
import numpy as np
import urllib
import base64


class ConstAPIName:
    SUGGEST_COMMANDS = "SUGGEST_COMMANDS"
    GET_RESPONSE = "GET_RESPONSE"
    GET_RESPONSE_STREAM = "GET_RESPONSE_STREAM"
    UNKNOWN = "UNKNOWN"


class RequestOrResponse:
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    UNKNOWN = "UNKNOWN"


REGEX_K =  re.compile(r'[\[](.*?)[\]]', re.S)


class LogItem:
    def __init__(self, _line):
        self.is_available = False

        self.request_or_response = RequestOrResponse.UNKNOWN
        self.date_time = datetime.datetime.now()
        self.api_name = ConstAPIName.UNKNOWN
        self.dict = {}

        self.is_available = self.parse_log(_line)

    def parse_log(self, _line):
        _items = [_item.strip() for _item in _line.split("]:")]
        _items_count = len(_items)
        if _items_count != 3:
            return False

        _log_header = _items[0] + "]"
        _req_header = _items[1] + "]"
        _json_body = _items[2]

        # parse date time
        self.date_time = self.parse_datetime_from_log_header(_log_header)
        if self.date_time is None:
            return False

        # parse request header
        self.request_or_response, self.api_name = self.parse_request_header(_req_header)
        # body dict
        try:
            self.dict = json.loads(_json_body)
            return True
        except:
            return False

    def parse_request_header(self, _req_header):
        _matches = REGEX_K.findall(_req_header)
        if len(_matches) != 2:
            return None
        _request_or_response = _matches[0].strip()
        _api_name = _matches[1].strip()
        return _request_or_response, _api_name

    def parse_datetime_from_log_header(self, _log_header):
        _matches = REGEX_K.findall(_log_header)
        if len(_matches) != 3:
            return None
        _date_time = datetime.datetime.strptime(_matches[0], "%Y-%m-%d %H:%M:%S,%f")
        return _date_time


def load_log_items(_log_dir):
    _log_path_names = glob.glob(r"%s/*.log" % _log_dir)
    _total_count = len(_log_path_names)
    _step = _total_count // 20
    _step = 1 if _step < 5 else _step

    _total_log_lines_count, _actual_log_lines_count = 0, 0
    _log_items = []
    for _idx, _log_path_name in enumerate(_log_path_names):
        if _idx % _step == 0:
            print("[%d/%d %.2f%%] log files have completed!" % (
                _idx, _total_count, _idx / _total_count * 100
            ))
        with open(_log_path_name, "r", encoding="utf-8") as _fin:
            for _line in _fin:
                _line = _line.strip()
                if _line == "":
                    continue

                _total_log_lines_count += 1

                _log_item = LogItem(_line)
                if not _log_item.is_available:
                    continue

                _log_items.append(_log_item)
                _actual_log_lines_count += 1

    print("Finished! # of total log Line: %d, # of actual log line: %d" % (
        _total_log_lines_count, _actual_log_lines_count
    ))

    return _log_items


class LogResponse:
    def __init__(self, _log_item):
        self.is_available = False

        self.log_item = _log_item
        if "body" not in self.log_item.dict.keys():
            return
        try:
            self.body_dict = json.loads(self.log_item.dict["body"])
        except:
            return
        self.is_available = True

    def is_succeed(self):
        if "Status_Code" not in self.body_dict.keys():
            return False
        return self.body_dict["Status_Code"] == "200"

    def get_raw_id(self):
        if "RawId" not in self.body_dict.keys():
            return "default"

        return self.body_dict["RawId"].strip()

    def get_date_time(self):
        return self.log_item.date_time


class LogRequest:
    def __init__(self, _log_item):
        self.is_available = False

        self.log_item = _log_item

        self.header_dict = self.parse_header(_log_item)
        if self.header_dict is None:
            print("header is empty in LogRequest!")
            return

        self.body_dict = self.parse_body(_log_item)

        if self.body_dict is None:
            return
        if "Command" not in self.body_dict.keys():
            return

        if "Task" not in self.body_dict.keys():
            return

        self.is_available = True


    def parse_header(self, _log_item):
        if "headers" not in _log_item.dict.keys():
            return None

        try:
            _header_dict = json.loads(_log_item.dict["headers"])
        except:
            return None
        return _header_dict

    def parse_body(self, _log_item):
        if _log_item.api_name == ConstAPIName.GET_RESPONSE:
            _body_dict = self.parse_body_for_response(_log_item)
        elif _log_item.api_name == ConstAPIName.GET_RESPONSE_STREAM:
            _body_dict = self.parse_body_for_stream_response(_log_item)
        return _body_dict

    def parse_body_for_response(self, _log_item):
        if "body" not in _log_item.dict.keys():
            return None

        try:
            _body_dict = json.loads(_log_item.dict["body"])
            if "Options" not in _body_dict.keys():
                _body_dict["Options"] = {}
        except:
            return None
        return _body_dict

    def parse_body_for_stream_response(self, _log_item):
        _raw_json = _log_item.dict["raw"]

        _prefix = "\'query_string\': b\'params="
        _start = _raw_json.find(_prefix)
        if _start < 0:
            return None

        _end = _raw_json.find("\',", _start)
        if _end <= _start:
            return None

        _base64_str = _raw_json[_start: _end]
        _base64_str = _base64_str.replace(_prefix, "")

        _bytes = base64.b64decode(_base64_str).decode("utf-8")
        _json_str = urllib.parse.unquote(_bytes, encoding="utf-8")
        _dict = json.loads(_json_str)

        return _dict

    def get_options(self):
        _options_dict = self.body_dict["Options"]
        return list(_options_dict.items())

    def get_command(self, _cut_off=50):
        _command = self.body_dict["Command"]
        if len(_command) > _cut_off:
            _command = _command[0: _cut_off] + " ..."
        return _command

    def get_task_name(self):
        return self.body_dict["Task"]

    def get_user_agent(self, _cut_off=100):
        if "User-Agent" not in self.header_dict.keys():
            return "Unknown"

        _user_agent = self.header_dict["User-Agent"]
        if len(_user_agent) > _cut_off:
            _user_agent = _user_agent[0: _cut_off] + " ..."
        return _user_agent

    def get_method(self):
        return self.header_dict["Method"]

    def get_raw_id(self):
        return self.header_dict["RawId"].strip()

    def get_date_time(self):
        return self.log_item.date_time


def filter_and_create_log_responses(
        _log_items, _api_name,
        _start_date=datetime.datetime.strptime("2023-01-20 10:00:00", "%Y-%m-%d %H:%M:%S")
):
    _log_responses = []

    for _log_item in _log_items:
        if _log_item.date_time >= _start_date \
            and _log_item.request_or_response == RequestOrResponse.RESPONSE \
                and _log_item.api_name == _api_name:

            _log_response = LogResponse(_log_item)
            if _log_response.body_dict is None or len(_log_response.body_dict) == 0:        # Workaround: to skip response for request with method = OPTIONS
                continue
            _log_responses.append(_log_response)

    return _log_responses


def filter_and_create_log_requests(
        _log_items, _api_name,
        _start_date=datetime.datetime.strptime("2023-01-20 10:00:00", "%Y-%m-%d %H:%M:%S")
):
    _log_requests = []

    for _log_item in _log_items:
        if _log_item.date_time >= _start_date \
            and _log_item.request_or_response == RequestOrResponse.REQUEST \
                and _log_item.api_name == _api_name:
            _log_request = LogRequest(_log_item)
            if _log_request.is_available:
                _log_requests.append(_log_request)

    return _log_requests


def count_success_and_failed(_log_responses):
    _succeed, _failed = 0, 0

    for _log_response in _log_responses:
        if _log_response.is_succeed:
            _succeed += 1
        else:
            _failed += 1

    return _succeed, _failed


def count_user_agent_and_task_and_command(_log_requests):
    _user_agent2count, _task2count, _command2count = {}, {}, {}

    for _log_request in _log_requests:
        _task_name = _log_request.get_task_name()
        if _task_name not in _task2count.keys():
            _task2count[_task_name] = 0
        _task2count[_task_name] += 1

        _user_agent = _log_request.get_user_agent()
        if _user_agent not in _user_agent2count.keys():
            _user_agent2count[_user_agent] = 0
        _user_agent2count[_user_agent] += 1

        _command = _log_request.get_command()
        if _command not in _command2count.keys():
            _command2count[_command] = 0
        _command2count[_command] += 1

    return _user_agent2count, _task2count, _command2count


def count_options(_log_requests):
    _option_name2value2count = {}

    for _log_request in _log_requests:
        _options = _log_request.get_options()
        for _name, _value in _options:
            if _value == "":
                continue
            if _name not in _option_name2value2count.keys():
                _option_name2value2count[_name] = {}
            if _value not in _option_name2value2count[_name].keys():
                _option_name2value2count[_name][_value] = 0
            _option_name2value2count[_name][_value] += 1

    return _option_name2value2count


def group_request_and_response_by_raw_id(_log_requests, _log_responses):

    _raw_id2log_response = {}
    for _log_response in _log_responses:
        _raw_id = _log_response.get_raw_id()
        _raw_id2log_response[_raw_id] = _log_response

    _raw_id2start_end = {}
    for _log_request in _log_requests:
        _req_raw_id = _log_request.get_raw_id()

        if _req_raw_id not in _raw_id2log_response.keys():
            continue

        _log_response = _raw_id2log_response[_req_raw_id]

        _raw_id2start_end[_req_raw_id] = [_log_request.get_date_time(), _log_response.get_date_time()]

    return _raw_id2start_end


def calculate_elapse(_log_requests, _log_responses):

    # get basic statistics
    _raw_id2start_end = group_request_and_response_by_raw_id(_log_requests, _log_responses)

    _elapses = []

    for _raw_id, _start_end in _raw_id2start_end.items():

        _start, _end = _start_end

        _delta = _end - _start

        _elapse = _delta.seconds * 1000 + _delta.microseconds / 1000

        _elapses.append(_elapse)

    if len(_elapses) == 0:
        return 0, 0, 0, {}, {}

    _max_elapse = max(_elapses)
    _min_elapse = min(_elapses)

    _aver_elapse = np.average(_elapses)


    # split by bucket
    _bucket2count = {"0-10": 0, "10-20": 0, "20-30": 0, "30-": 0}
    for _elapse in _elapses:        
        if _elapse <= 10000:
            _bucket2count["0-10"] += 1
        elif _elapse <= 20000:
            _bucket2count["10-20"] += 1
        elif _elapse <= 30000:
            _bucket2count["20-30"] += 1
        else:
            _bucket2count["30-"] += 1

    _bucket2freq = {}
    for _bucket, _count in _bucket2count.items():
        _bucket2freq[_bucket] = _count / len(_elapses) * 100

    return _max_elapse, _min_elapse, _aver_elapse, _bucket2count, _bucket2freq


def make_statistics():

    _log_dir = r"debug_log"
    _log_items = load_log_items(_log_dir)

    _stats_str = " ===================== [STATISTICS BEGIN] ========================= \n"

    _log_stream_requests = filter_and_create_log_requests(_log_items, ConstAPIName.GET_RESPONSE_STREAM)

    _stats_str += "Stream Requests: %d\n" % len(_log_stream_requests)

    _log_requests = filter_and_create_log_requests(_log_items, ConstAPIName.GET_RESPONSE)
    _stats_str += "Common Requests: %d\n" % len(_log_requests)

    _log_requests += _log_stream_requests

    _log_responses = filter_and_create_log_responses(_log_items, ConstAPIName.GET_RESPONSE)
    _succeed, _failed = count_success_and_failed(_log_responses)

    _stats_str += "Responses: %d\n" % len(_log_responses)
    _stats_str += "    | - Succeed: %d\n" % _succeed
    _stats_str += "    | - Failed : %d\n" % _failed
    _stats_str += "\n"

    _max_elapse, _min_elapse, _aver_elapse, _bucket2count, _bucket2freq = calculate_elapse(_log_requests, _log_responses)
    _table = PrettyTable(["Command", "Min Elapse", "Max Elapse", "Aver Elapse"])
    _table.add_row(["GET_RESPONSE", "%.6f ms" % _min_elapse, "%.6f ms" % _max_elapse, "%.6f ms" % _aver_elapse])
    _stats_str += "%s\n" % _table

    _buckets = list(_bucket2count.keys())
    _count_strs, _freq_strs = ["count"], ["freq"]
    for _bucket in _buckets:
        _count_strs.append("%s" % _bucket2count[_bucket])
        _freq_strs.append("%.2f%%" % _bucket2freq[_bucket])

    _table = PrettyTable([""] + _buckets)
    _table.add_row(_count_strs)
    _table.add_row(_freq_strs)
    _stats_str += "%s\n" % _table

    _user_agent2count, _task2count, _command2count = count_user_agent_and_task_and_command(_log_requests)
    _table = PrettyTable(["User Agent", "Count"])
    for _user_agent, _count in sorted(_user_agent2count.items(), key=lambda x: x[1], reverse=True):
        _table.add_row([_user_agent, _count])
    _table.align[_table.field_names[0]] = "l"
    _stats_str += "%s\n" % _table

    _table = PrettyTable(["Task", "Count"])
    for _task, _count in sorted(_task2count.items(), key=lambda x: x[1], reverse=True):
        _table.add_row([_task, _count])
    _table.align[_table.field_names[0]] = "l"
    _stats_str += "%s\n" % _table

    _table = PrettyTable(["Command", "Count"])
    for _command, _count in sorted(_command2count.items(), key=lambda x: x[1], reverse=True):
        _table.add_row([_command, _count])
    _table.align[_table.field_names[0]] = "l"
    _stats_str += "%s\n" % _table

    _option_name2value2count = count_options(_log_requests)
    _table = PrettyTable(["Option Name", "Value", "Count"])
    for _option_name, _value2count in _option_name2value2count.items():
        for _value, _count in sorted(_value2count.items(), key=lambda x: x[1], reverse=True):
            _table.add_row([_option_name, _value, _count])
    _table.align[_table.field_names[0]] = "l"
    _table.align[_table.field_names[1]] = "l"
    _stats_str += "%s\n" % _table

    _stats_str += " ====================== [STATISTICS END] ========================== \n"

    return _stats_str


if __name__ == "__main__":
    _stats_str = make_statistics()
    print(_stats_str)
