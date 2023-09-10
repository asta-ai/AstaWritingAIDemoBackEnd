import os
import openai
import requests
import json


def init_openai():
    openai.organization = "org-hilD9mPrUa80Vn4ZLTGceYFK"
    openai.api_key = "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"


def request_openai(_prompt):
    _headers = {
        'Content-Type': 'application/json', 
        'Authorization': 'Bearer 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', 
        'OpenAI-Organization': 'org-hilD9mPrUa80Vn4ZLTGceYFK'
        }

    _url = 'https://api.openai.com/v1/completions'


    _body = {
        "model": "text-davinci-003",
        "prompt": "%s" % _prompt,
        "max_tokens": 1024,
        "temperature": 0.6
    }

    _response = requests.post(url=_url, headers = _headers, data = json.dumps(_body))

    _response_json = ""
    _status_code = _response.status_code
    if _status_code == 200:
        _response_json = _response.text
    else:
        print("Failed to request, status_code: %s" % _status_code)
        _response_json = "调用API发生错误! status_code: %s" % _status_code
    return _status_code, _response_json        


def mock_request_openai(_prompt):
    with open("response_title.json", "r") as _fin:
        return 200, _fin.read().strip()

def generate_title(_prompt, _top_n=3):
    _prompt += "\r\n语言：中文"
    _prompt += "\r\n根据上面的内容生成%d个标题：" % _top_n

    _status_code, _response_json = request_openai(_prompt)
    # _status_code, _response_json = mock_request_openai(_prompt)

    _title = _response_json
    if _status_code:
        _dict = json.loads(_response_json)
        _title = _dict['choices'][0]['text'].strip()

    return _title


def generate_paragraph(_prompt):
    _prompt += "\r\n语言：中文"
    _prompt += "\r\n根据上面的内容生成一篇营销文章："

    _status_code, _response_json = request_openai(_prompt)
    # _status_code, _response_json = mock_request_openai(_prompt)

    _paragraph = _response_json
    if _status_code:
        _dict = json.loads(_response_json)
        _paragraph = _dict['choices'][0]['text'].strip()

    return _paragraph

def main():
    init_openai()

    _prompt = "文章内容：佳能单反相机EOS 5D Mark IV"
    #_title = generate_title(_prompt)
    
    _paragraph = generate_paragraph(_prompt)
    print(_paragraph)

main()

