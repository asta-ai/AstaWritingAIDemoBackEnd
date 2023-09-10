import openai
from flask import Flask, request, render_template, make_response, Response
import json
import time
import random
from prompt_creator import PromptCreator
from openai_utils import OpenAIUtils
from logger import sys_logger
import uuid
import re
import datetime
import os
import sys
import base64
import fitz
import docx
import openai


class ConstTaskName:
    XIAO_HONG_SHU = "Xiaohongshu"
    LS_SCRIPT = "LSScript"
    NEW_YEAR = "NewYear"
    ANSWER = "QuestionAnswer"
    IMITATE = "Imitate"
    REWRITE = "Rewrite"

    @staticmethod
    def get_available_task_names():
        return [ConstTaskName.XIAO_HONG_SHU, ConstTaskName.LS_SCRIPT, ConstTaskName.NEW_YEAR, ConstTaskName.ANSWER, ConstTaskName.IMITATE, ConstTaskName.REWRITE]

    @staticmethod
    def is_available_task_name(_task_name):
        return _task_name in ConstTaskName.get_available_task_names()


class InternalResponse:
    def __init__(self, _internal_request):
        self.internal_request = _internal_request

    def add_cors_header(self, _response):
        _response.headers['Access-Control-Allow-Origin'] = '*'
        _response.headers['Access-Control-Allow-Methods'] = '*'
        _response.headers['Access-Control-Expose-Headers'] = 'X-Requested-With'
        _response.headers['Access-Control-Allow-Headers'] = '*'
        return _response

    def get_response(self):
        raise "get_response in base class is not implemented:!"

    def create_response(self, _dict, _status_code, _is_add_cors_header=True):
        _response = make_response(json.dumps(_dict, ensure_ascii=False)) 
        _response.status = _status_code
        if _is_add_cors_header:
            _response = self.add_cors_header(_response)
        return _response

    def create_dict_for_response(self, _error_code = "200", _error_msg = "成功"):
        _dict = {
            "Status_Code": _error_code,
            "ErrorMsg": _error_msg
        }
        if self.internal_request is not None:
            _dict["RawId"] = self.internal_request.header.raw_id()
            _dict["RequestId"] = self.internal_request.header.request_id()
            _dict["User"] = self.internal_request.header.user()

        return _dict


class MockedInternalCompletionResponse(InternalResponse):
    def __init__(self, _internal_request):
        super().__init__(_internal_request)

    def get_response(self):
        
        _sec = random.randint(3, 6)
        time.sleep(_sec)
        
        _task_name = self.internal_request.body.task()

        _status_code = "200"
        if _task_name == ConstTaskName.XIAO_HONG_SHU:
            _dict = {
                "Status_Code": _status_code,
                "ErrorMsg": "成功",
                "RequestId": self.internal_request.header.request_id(),
                "User": self.internal_request.header.user(),
                "Text": "[DEBUG: 小红书] 冷泡茶，这可是一种独特的饮品！它可以让你在炎热的夏天里拥有一杯清凉可口的茶饮，而不需要一般泡茶的麻烦。它的制作方法简单易行，只需要将茶叶放入凉水中浸泡，然后放入冰箱冷藏即可。冷泡茶里面的茶叶有着清新的香气，而且口感清爽，可以提神又消暑，是夏日里一杯不可或缺的茶饮。"

            }
        elif _task_name == ConstTaskName.NEW_YEAR or _task_name == ConstTaskName.ANSWER:
            _dict = {
                "Status_Code": _status_code,
                "ErrorMsg": "成功",
                "RequestId": self.internal_request.header.request_id(),
                "User": self.internal_request.header.user(),
                "Text": "[DEBUG: 新年寄语] 新年快乐！在兔年里，让我们把握每一分每一秒，勇敢地去追求自己的梦想，珍惜身边的家人和朋友，共同创造更美好的明天！"
            }
        elif _task_name == ConstTaskName.LS_SCRIPT:
            _text = """
                开场：
                    漂亮的妆容，总是离不开一支精致的口红！
                第一段：
                    口红是女性化妆必备的美妆神器，它不仅可以增加她们的魅力，还能让妆容更加完美。不同的口红颜色可以带来不同的妆容效果，从清新的粉色、热情的红色，到有趣的橘色，总有一款适合你！
                第二段：
                    选择口红时，一定要选择恰当的质地，润泽滋润的口红，能够滋润唇部，带来舒适的触感，久久不脱色，让妆容持久维持。另外，还要注意口红的颜色和肤色搭配，搭配得当，才能让妆容更加完美！
                结尾：
                    选对口红，美丽不费力！妆容完美，从一支口红开始！
                """
            _dict = {
                "Status_Code": _status_code,
                "ErrorMsg": "成功",
                "RequestId": self.internal_request.header.request_id(),
                "User": self.internal_request.header.user(),
                "Text": "[DEBUG: 直播脚本] %s" % _text
            }
        else:
            _status_code = "500"
            _dict = {
                "Status_Code": _status_code,
                "ErrorMsg": "Unknown Task Name: %s" % _task_name ,
                "RequestId": self.internal_request.header.request_id(),
                "User": self.internal_request.header.user(),
                "Text": ""
            }

        _response = self.create_response(_dict, _status_code, _is_add_cors_header=True)

        return _response


class InternalSuggCMDResponse(InternalResponse):
    def __init__(self, _internal_request):
        super().__init__(_internal_request)

        self.task2commands = self.load_commands()

    def load_commands_from_file(self, _file_path_name):
        _commands = []
        with open(_file_path_name, "r", encoding="utf-8") as _fin:
            for _line in _fin:
                _line = _line.strip()
                if _line == "":
                    continue
                _commands.append(_line)
        return _commands

    def load_commands(self):
        _task2commands = {}
        _task2commands[ConstTaskName.XIAO_HONG_SHU] = self.load_commands_from_file(r"./data/commands/xhs.txt")
        _task2commands[ConstTaskName.NEW_YEAR] = self.load_commands_from_file(r"./data/commands/new_year.txt")
        _task2commands[ConstTaskName.LS_SCRIPT] =self.load_commands_from_file(r"./data/commands/ls_script.txt")
        _task2commands[ConstTaskName.ANSWER] =self.load_commands_from_file(r"./data/commands/answer.txt")
        _task2commands[ConstTaskName.REWRITE] =self.load_commands_from_file(r"./data/commands/rewrite.txt") 
        _task2commands[ConstTaskName.IMITATE] =self.load_commands_from_file(r"./data/commands/imitate.txt")
        return _task2commands

    def get_top_n_commands_randomly(self, _top_n, _commands):
        _commands_count = len(_commands)
        if _commands_count <= _top_n:
            return _commands
        
        random.shuffle(_commands)

        return _commands[0: _top_n]

    def get_response(self):    

        # get task name
        _task_name = self.internal_request.body.task()

        # is task name available 
        _status_code = "200" 

        if ConstTaskName.is_available_task_name(_task_name):
            # randomly get top 3 commands
            _commands = self.get_top_n_commands_randomly(_top_n=3, _commands=self.task2commands[_task_name])
            
            # create dict for response
            _dict = self.create_dict_for_response()
            _dict["Commands"] = _commands

            _status_code = "200" 

        else:
            _status_code = "500"
            _dict = self.create_dict_for_response(_status_code, "Unknown Task Name: %s" % _task_name)

        # create response
        _response = self.create_response(_dict, _status_code, _is_add_cors_header=True)

        return _response


class InternalOptionsResponse (InternalResponse):
    def __init__(self, _internal_request):
        super().__init__(_internal_request)

    def get_response(self):
        
        _dict = {}
        _response = self.create_response(_dict, "200", _is_add_cors_header=True)

        return _response

class InternalErrorResponse(InternalResponse):
    def __init__(self, _error_code, _error_msg, _internal_request=None):
        super().__init__(_internal_request)

        self.error_code = _error_code
        self.error_msg = _error_msg

    def get_response(self):
        _dict = {
            "Status_Code": self.error_code,
            "ErrorMsg": self.error_msg 
        }

        if self.internal_request is not None:
            _dict["RequestId"] = self.internal_request.header.request_id()
            _dict["User"] = self.internal_request.header.user()

        _response = self.create_response(_dict, "500", _is_add_cors_header=True)

        return _response


class InternalCompletionResponse(InternalResponse):
    def __init__(self, _internal_request):
        super().__init__(_internal_request)

    def get_response(self):
        
        _task_name = self.internal_request.body.task()

        _status_code = "200" 

        if ConstTaskName.is_available_task_name(_task_name):

            _context = self.internal_request.body.get_context()
            
            _option_name2value = self.internal_request.body.get_option_name2value()

            _command = self.internal_request.body.get_command()

            _prompt_creator = PromptCreator(_task_name, _context, _option_name2value, _command)
            
            _prompt = _prompt_creator.create_prompt()
            
            print("==================> Prompt: %s" % _prompt)

            _model_params = {}
            #if _task_name == ConstTaskName.LS_SCRIPT:
            #    _model_params["n"] = 1              # return 1 text if the task is LS_SCRIPT
            #else:
            #    _model_params["n"] = 2
            _model_params["n"] = 1
            _status_code, _openai_response_json = OpenAIUtils.request(_prompt, _model_params)

            _status_code = "%s" % _status_code
            _error_msg = "成功"
            if _status_code != "200":
                _error_msg = "Failed to call model!"

            _openai_dict = json.loads(_openai_response_json)
            
            if "choices" not in _openai_dict.keys() or len(_openai_dict["choices"]) == 0:
                _status_code = "500"
                _dict = self.create_dict_for_response(_status_code, "Not key \"Choices\" in OpenAI Response")
            else:
                _texts = [_d['text'] for _d in _openai_dict['choices']]
                _text = "[SEPARATE]".join(_texts)

                _dict = self.create_dict_for_response(_status_code,  _error_msg)

                _dict["Text"] = _text

                _dict["Debug"] = {
                    "PromptToOpenAI": _prompt,
                    "Text": _text
                }
                print("Call Open AI ============================================= ")
                print("Prompt To Open AI: %s" % _prompt)
                print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ ")
                print("Text from Open AI: %s" % _text)
                print("------------------------------------------------------------ ")
                print("Raw response json from Open AI:", _openai_response_json)

        else:
            _status_code = "500"
            _dict = self.create_dict_for_response(_status_code, "Unknown Task Name: %s" % _task_name)

        _response = self.create_response(_dict, _status_code, _is_add_cors_header=True)

        return _response


class InternalStreamCompletionResponse(InternalResponse):

    def __init__(self, _internal_request):
        super().__init__(_internal_request)

        self.response_text = ""
        self.prompt = ""
        self.response = None

    def get_response(self):

        def stream_proc(_prompt):
            
            print("========================")
            print("Raw Stream Prompt: " + _prompt)
            print("++++++++++++++++++++++++")
            _prompt = _prompt.replace("\r", "")
            _prompt = re.sub("\n+", "\n", _prompt)
            _prompt = _prompt.replace("<p>", "").replace("</p>", "").replace("\n", "\\r\\n")
            print("Normalized Stream Prompt: " + _prompt)
            print("========================")
            _model_params = OpenAIUtils.get_model_parameters()
            openai.api_key = OpenAIUtils.API_KEY
            openai.organization = OpenAIUtils.OPENAI_ORGANIZATION

            _messages=[
                {"role": "system", "content": "你是一个写作助手。你的任务是帮助用户写出行文优美的优秀的内容。"},
                {"role": "user", "content": _prompt}
            ]
            
            print(_prompt)
            
            #_completion = openai.Completion.create(
            _completion = openai.ChatCompletion.create(
                #engine=OpenAIUtils.MODEL_NAME,
                #prompt=_prompt,
                model="gpt-3.5-turbo",
                messages=_messages,
                max_tokens=_model_params["max_tokens"],
                temperature=_model_params["temperature"],
                presence_penalty=_model_params["presence_penalty"],
                frequency_penalty=_model_params["frequency_penalty"],
                n=_model_params["n"],
                stop=None,
                stream=True
            )


            _is_stop = False
            self.response_text = ""
            self.prompt = _prompt
            _working_id = str(uuid.uuid1())

            for _response_dict in _completion:
                print(_response_dict)
                if len(_response_dict["choices"]) <= 0:
                    continue
                
                _response_text = ""
                if "delta" in _response_dict["choices"][0].keys() and "content" in _response_dict["choices"][0]["delta"].keys():
                    _response_text = _response_dict["choices"][0]["delta"]["content"]
                elif "text" in _response_dict["choices"][0].keys():
                    _response_text = _response_dict["choices"][0]["text"]
                
                _is_stop = False
                if "finish_reason" in _response_dict["choices"][0].keys():
                    _is_stop = _response_dict["choices"][0]["finish_reason"] == "stop"
                print("Is Stop: %s" % _is_stop)
                if _is_stop == True:
                    _response_text = "[DONE]"
                print("stream data: " + _response_text)

                if _response_text.strip() == "":
                    continue

                self.response_text += _response_text

                _response_text = "data: %s\n\n" % _response_text
                print("_response_text ==> %s" % _response_text)
                ### DEBUG LOG === 
                _dict = {}

                _dict["Text"] = _response_text
    
                _dict["Debug"] = {
                    "PromptToOpenAI": self.prompt,
                    "Text": _response_text
                }
    
                _body_json_str = json.dumps(_dict)
                _dict = {
                    "headers":"" if self.internal_request is None else json.dumps(self.internal_request.header.key2value),
                    "body": _body_json_str,
                    "raw": _response_text,
                    "working_id": _working_id
                }
            
                _json = json.dumps(_dict, ensure_ascii=False).strip()
                sys_logger.info("[RESPONSE][GET_RESPONES_STREAM_WORKING]: %s" % _json)
                
                yield _response_text

              # create a response for logging
            _dict = {}

            _dict["Text"] = self.response_text

            _dict["Debug"] = {
              "PromptToOpenAI": self.prompt,
              "Text": self.response_text
            }

            _body_json_str = json.dumps(_dict)
            _dict = {
              "headers":"" if self.internal_request is None else json.dumps(self.internal_request.header.key2value),
              "body": _body_json_str,
              "raw": _response_text,
              "working_id": _working_id
            }

            _json = json.dumps(_dict, ensure_ascii=False).strip()
            sys_logger.info("[RESPONSE][GET_RESPONES_STREAM_AFTER]: %s" % _json)

            # send a [DONE]
            if not _is_stop:
              ### DEBUG LOG ===
              _response_text = "data: [DONE]\n\n"

              _dict = {}

              _dict["Text"] = _response_text

              _dict["Debug"] = {
                "PromptToOpenAI": self.prompt,
                "Text": _response_text
              }

              _body_json_str = json.dumps(_dict)
              _dict = {
                "headers":"" if self.internal_request is None else json.dumps(self.internal_request.header.key2value),
                "body": _body_json_str,
                "raw": _response_text,
                "working_id": _working_id
              }

              _json = json.dumps(_dict, ensure_ascii=False).strip()
              sys_logger.info("[RESPONSE][GET_RESPONES_STREAM_WORKING]: %s" % _json)

              print("Stream Stopped!")
              return _response_text



        _task_name = self.internal_request.body.task()

        _status_code = "200"

        if ConstTaskName.is_available_task_name(_task_name):

            _context = self.internal_request.body.get_context()

            _option_name2value = self.internal_request.body.get_option_name2value()

            _command = self.internal_request.body.get_command()

            _prompt_creator = PromptCreator(_task_name, _context, _option_name2value, _command)

            _prompt = _prompt_creator.create_prompt()

            _response = Response(stream_proc(_prompt), mimetype='text/event-stream')

            self.add_cors_header(_response)

            self.response = _response

        else:
            _status_code = "500"
            _dict = self.create_dict_for_response(_status_code, "Unknown Task Name: %s" % _task_name)
            _response = self.create_response(_dict, _status_code, _is_add_cors_header=True)

        return _response

        
class InternalTelementryResponse(InternalResponse):
    def __init__(self, _error_code="200", _error_msg="成功", _internal_request=None):
        super().__init__(_internal_request)

        self.error_code = _error_code
        self.error_msg = _error_msg

    def get_response(self):
        _dict = {
            "Status_Code": self.error_code,
            "ErrorMsg": self.error_msg 
        }

        if self.internal_request is None:
            _dict["RequestId"] = self.internal_request.header.request_id()
            _dict["User"] = self.internal_request.header.user()

        _response = self.create_response(_dict, self.error_code, _is_add_cors_header=True)

        return _response


class InternalParseFileContentResponse(InternalResponse):
    ALLOWED_FILE_TYPE = ["doc", "docx", "pdf", "txt", "mp4"]
    KEY_NAME_FILE_TYPE = "File_Type"
    KEY_NAME_BASE64_CONTENT = "Base64_Content"
    TAKE_NAME = "ParseFileContent"
    def __init__(self, _internal_request):
        super().__init__(_internal_request)

        # check support
        self.error_code = "200"
        self.error_msg = ""

        # check task
        if self.internal_request.body.task() != InternalParseFileContentResponse.TAKE_NAME:
            self.error_code = "500"
            self.error_msg = "Not supported task: %s" % self.internal_request.body.task()
            return False

        self.file_type = self.get_file_type()

        self.is_available = self.check_support_file_type(self.file_type)
        if not self.is_available:
            self.error_code = "500"
            self.error_msg = "Not supported file type: %s" % self.file_type
            return

        # upload file to folder
        self.upload_path_name = self.get_upload_path_name()

        self.is_available = self.save_file(self.upload_path_name)
        if not self.is_available:
            self.error_code = "500"
            self.error_msg = "Failed to save file to %s" % self.upload_path_name

        # convert doc to docx
        if self.file_type == "doc":
            print("Converting doc to docx ... ")
            _dir_name, _file_name = os.path.split(self.upload_path_name)
            _cmd = "soffice --convert-to docx --headless --invisible %s --outdir %s" % (
                self.upload_path_name, _dir_name
            )
            print(_cmd)
            os.system(_cmd)

            self.upload_path_name = "%sx" % self.upload_path_name
            if not os.path.exists(self.upload_path_name):
                print("Failed to convert file doc to docx!")
                self.error_code = "500"
                self.error_msg = "Failed to convert doc: %s" % self.upload_path_name
                self.is_available = False
            else:
                print("Finished Converting! docx: %s" % self.upload_path_name)

    def save_file(self, _upload_path_name):

        # get base64 content
        _base64_content = self.internal_request.body.get_value_by_key(InternalParseFileContentResponse.KEY_NAME_BASE64_CONTENT)
        _base64_content = _base64_content.strip()

        if _base64_content == "":
            return False

        # convert to bytes
        _bytes = base64.b64decode(_base64_content)
        if _bytes is None or len(_bytes) == 0:
            return False

        # save to file
        with open(_upload_path_name, "wb") as _fout:
            _fout.write(_bytes)
        return True

    def get_file_type(self):
        _file_type = self.internal_request.body.get_value_by_key(InternalParseFileContentResponse.KEY_NAME_FILE_TYPE)
        return _file_type.lower()


    def check_support_file_type(self, _file_type):
        return _file_type in InternalParseFileContentResponse.ALLOWED_FILE_TYPE

    def get_upload_path_name(self):

        _now = datetime.datetime.now()
        _dir_name = os.path.join("upload", _now.strftime(r"%Y_%m_%d_%H"))
        if not os.path.exists(_dir_name):
            os.makedirs(_dir_name)
        _file_name = "%s.%s" % (
            str(uuid.uuid1()),
            self.file_type
        )
        _upload_path_name = os.path.join(_dir_name, _file_name)
        return _upload_path_name


    def get_response(self):
        
        # not available
        if not self.is_available:
            _dict = self.create_dict_for_response(self.error_code, self.error_msg)
            _response = self.create_response(_dict, self.error_code, _is_add_cors_header=True)
            return _response

        # parse content
        _content, _parser_name, _internal_error_msg = self.parse_content()
        if _content is None:
            self.error_code = "500"
            self.error_msg = "Failed to parse content from file! Internal Error Msg: %s" % _internal_error_msg
            _dict = self.create_dict_for_response(self.error_code, self.error_msg)
            _response = self.create_response(_dict, self.error_code, _is_add_cors_header=True)
            return _response

        # create response
        _dict = self.create_dict_for_response(self.error_code, self.error_msg)
        _dict["Content"] = _content
        _dict["Upladed_File_Path"] = self.upload_path_name
        _dict["Parser"] = _parser_name
        _response = self.create_response(_dict, self.error_code, _is_add_cors_header=True)

        return _response

    def parse_content(self, _is_return_internel_error_msg=True):
        _content = None
        _parser_name = ""
        _error_msg = ""
        try:
            if self.file_type == "pdf":
                _content = self.parse_pdf(self.upload_path_name)
                _parser_name = "fitz"
            elif self.file_type == "txt":
                _content = self.parse_txt(self.upload_path_name)
                _parser_name = "python"
            elif self.file_type == "docx" or self.file_type == "doc":
                _content = self.parse_docx(self.upload_path_name)
                _parser_name = "python-docx"
            elif self.file_type == "mp4":
                _content = self.parse_audio(self.upload_path_name)
                _parser_name = "whisper-1"
        except Exception as e:
            _content = None
            _error_msg += "=> %s" % str(e)

        if _is_return_internel_error_msg:
            return _content, _parser_name, _error_msg
        return _content, _parser_name

    def parse_pdf(self, _upload_path_name):
        _content = ""

        _doc = fitz.open(_upload_path_name)

        for _page in _doc:
            _text = _page.get_text("text")
            _content = "%s\r\n%s" % (_content, _text)
        
        return _content.strip()

    def parse_txt(self, _upload_path_name):
        _content = ""
        with open(_upload_path_name, "r", encoding = "utf-8") as _fin:
            _content = _fin.read()
        return _content

    def parse_docx(self, _upload_path_name):
        _content = ""
        _doc = docx.Document(_upload_path_name)
        for _para in _doc.paragraphs:
            _content = "%s\r\n%s" % (_content, _para.text)
        return _content
        
    def parse_audio(self, _upload_path_name):
        _content = ""
        with open(_upload_path_name, "rb") as _fin:
            openai.api_key = OpenAIUtils.API_KEY
            openai.organization = OpenAIUtils.OPENAI_ORGANIZATION
            _response = openai.Audio.transcribe("whisper-1", _fin)
            if _response is None or _response.text is None:
                return None
            _content = _response.text
        return _content
