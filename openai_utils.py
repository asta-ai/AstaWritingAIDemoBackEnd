import json
import openai
import requests

class OpenAIUtils:

    API_KEY = "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"
    OPENAI_ORGANIZATION = "org-XhegQkM7fdaW8ZzPSkCkzHE5"
    API_URL = "https://api.openai.com/v1/completions"

    MODEL_NAME = "text-davinci-003"                 # asta-ai-finetuned-text-davinci-003

    @staticmethod
    def request(_prompt, _override_model_params=None):
        
        _headers = OpenAIUtils.create_header()

        _model_params = OpenAIUtils.get_model_parameters()    

        if _override_model_params is not None:
            for _name, _value in _override_model_params.items():
                _model_params[_name] = _value

        print("Model Params: ")
        print(_model_params)

        _model_params["prompt"] = _prompt

        _response = requests.post(url=OpenAIUtils.API_URL, headers = _headers, data = json.dumps(_model_params))

        _response_json = ""
        _status_code = _response.status_code
        if _status_code == 200:
            _response_json = _response.text
        else:
            print("Failed to request, status_code: %s" % _status_code)
            _response_json = "调用API发生错误! status_code: %s" % _status_code

        return _status_code, _response_json     

    @staticmethod
    def create_header():
        _headers = {
            'Content-Type': 'application/json', 
            'Authorization': 'Bearer %s' % OpenAIUtils.API_KEY, 
            'OpenAI-Organization': '%s' % OpenAIUtils.OPENAI_ORGANIZATION
        }
        return _headers

    @staticmethod
    def get_model_parameters(_top_n=1):
        _body = {
            "model": OpenAIUtils.MODEL_NAME,
            "max_tokens": 2048,
            "temperature": 0.5,
            "presence_penalty": 1.0,            # 惩罚已经出现在文本中的token，出现则被惩罚
            "frequency_penalty": 1.0,           # 惩罚已经出现在文本中的token，根据出现频率惩罚
            "n": _top_n                         # 返回N个Result
        }
        return _body
