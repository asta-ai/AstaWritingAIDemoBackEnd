from flask import Flask, request, render_template, make_response
import json


class InternalRequestHeader:
    def __init__(self, _name_values):
        
        self.key2value = {_name.lower(): _value for _name, _value in _name_values}

    def request_id(self):
        if "requestid" not in self.key2value.keys():
            return "default"

        return self.key2value["requestid"]

    def raw_id(self):
        if "rawid" not in self.key2value.keys():
            return "default"

        return self.key2value["rawid"]

    def user(self):
        if "user" not in self.key2value.keys():
            return "default"
        return self.key2value["user"]
    
    def environment(self):
        if "environment" not in self.key2value.keys():
            return "defalut"
        return self.key2value["environment"]

class InternalRequestBody:

    FIELD_NAME_TASK = "Task"
    FIELD_NAME_OPTIONS = "Options"
    FIELD_NAME_CONTEXT = "Context"
    FIELD_NAME_COMMAND = "Command"

    def __init__(self, _body_json):
        self.name2value = json.loads(_body_json)

    def task(self):
        if InternalRequestBody.FIELD_NAME_TASK not in self.name2value.keys():
            return "default"
        return self.name2value[InternalRequestBody.FIELD_NAME_TASK]

    def get_context(self):
        if InternalRequestBody.FIELD_NAME_CONTEXT not in self.name2value.keys():
            return ""
        return self.name2value[InternalRequestBody.FIELD_NAME_CONTEXT]


    def get_option_name2value(self):
        if InternalRequestBody.FIELD_NAME_OPTIONS not in self.name2value.keys():
            return {}
        return self.name2value[InternalRequestBody.FIELD_NAME_OPTIONS]
    
    def get_command(self):
        if InternalRequestBody.FIELD_NAME_COMMAND not in self.name2value.keys():
            return []
        return self.name2value[InternalRequestBody.FIELD_NAME_COMMAND]

    def get_value_by_key(self, _key_name):
        if _key_name not in self.name2value.keys():
            return ""
        return self.name2value[_key_name]
    


class InternalRequest:
    def __init__(self, _header, _body):
        self.header = _header
        self.body = _body

    @staticmethod
    def create_request(_request, _body_json=None):
        # create header
        _header = InternalRequestHeader(list(_request.headers))
        
        # create body
        if _body_json is None:
            _body_json = _request.get_data().decode(encoding='utf-8').strip()
        _body = InternalRequestBody(_body_json)
        _internal_request = InternalRequest(_header, _body)

        return _internal_request