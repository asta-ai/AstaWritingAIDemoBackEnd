
from gevent import monkey
monkey.patch_all()
from flask import Flask, request, render_template
import argparse
from gevent import pywsgi
import os
import requests
import openai
import json

class logger:
    def __init__(self, _log_dir="log"):
        if not os.path.exists(_log_dir):
            os.makedirs(_log_dir)


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


def generate_idea(_prompt, _top_n=5):
    _prompt += "\r\n语言：中文"
    _prompt += "\r\n根据上面的内容生成%d个ideas：" % _top_n

    _status_code, _response_json = request_openai(_prompt)
    # _status_code, _response_json = mock_request_openai(_prompt)

    _idea = _response_json
    if _status_code:
        _dict = json.loads(_response_json)
        _idea = _dict['choices'][0]['text'].strip()

    return _idea


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


def generate_debug_content(_prompt):
    
    _status_code, _response_json = request_openai(_prompt)

    _paragraph = _response_json
    if _status_code:
        _dict = json.loads(_response_json)
        _paragraph = _dict['choices'][0]['text'].strip()

    return _paragraph


def navigate_to_new_task_page(_form):
    _task_name = get_task_name_from_form(_form)

    _page_name = "index.html"
    if _task_name == "opt_btn_bs":
        _page_name = "index.html"
    elif _task_name == "opt_btn_seo":
        _page_name = "index_seo.html"
    elif _task_name == "opt_btn_3sec":
        _page_name = "index_3sec.html"

    return _page_name


def get_task_name_from_form(_form):
    _task_name = _form.get("select")
    return _task_name

def start_sever():
    print("Starting server ... ")
    app = Flask(__name__)

    _http_id = "0.0.0.0"
    _port = 8888

    #@app.route('/')
    @app.route('/title-generation', methods=['GET', 'POST'])
    def response_request():
        if request.method == 'POST':

            if request.form.get("btn_select_task") is not None:
                _page_name = navigate_to_new_task_page(request.form)
                return render_template(_page_name)
            else:
                
                content = request.form.get('content')
                print("Content from POST request: %s" % content)

                _task_name = get_task_name_from_form(request.form)
                
                if _task_name == "opt_btn_bs" and request.form.get('btn_bs_gen') is not None:
                    _generated_content = generate_idea(content)
                    return render_template("index_ok.html", content=content, titles=_generated_content)
                elif _task_name == "opt_btn_seo" or _task_name == "opt_btn_3sec":
                    _generated_content = ""
                    if request.form.get('btn_content_gen') is not None:
                        _generated_content = generate_paragraph(content)
                    elif request.form.get("btn_title_gen") is not None:
                        _generated_content = generate_title(content)
                    else:
                        _generated_content = ""

                    if _task_name == "opt_btn_seo":
                        return render_template("index_seo_ok.html", content=content, titles=_generated_content)
                    elif _task_name == "opt_btn_3sec":
                        return render_template("index_3sec_ok.html", content=content, titles=_generated_content)
        return render_template("index.html")

    @app.route('/debug', methods=['GET', 'POST'])
    def response_request_debug():
        if request.method == 'POST':
            content = request.form.get('content')
            print("Content (Debug) from POST request: %s" % content)
            if request.form.get('btn_debug_gen') is not None:
                _generated_content = generate_debug_content(content)
                return render_template("index_debug_ok.html", content=content, titles=_generated_content)
        return render_template("index_debug.html")

    server = pywsgi.WSGIServer((_http_id, _port), app)
    print("Listening, ipaddr: %s, port: %d" % (_http_id, _port))
    server.serve_forever()
    print("Stop listening!")


if __name__ == '__main__':

    init_openai()

    start_sever()

