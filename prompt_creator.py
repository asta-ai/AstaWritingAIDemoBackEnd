from flask import Flask, request

class PromptCreator:
    def __init__(self, _task_name, _context, _option_name2value, _command):
        self.task_name = _task_name
        self.context = _context
        self.option_name2value = _option_name2value
        self.command = _command

    def create_prompt(self):
        
        _command = self.command

        _expression = self.get_tone_or_expression()
        if _expression != "":
            _command = "用%s的语气，%s" % (
                self.get_tone_or_expression(),
                self.command
            )

        _prompt = "\r\n".join(
            [
                self.get_options_text(),           # options
                self.context,
                "%s:" % _command
            ]
        )
        return _prompt

    def get_options_text(self):
        _options_text = "语言: 中文"
        for _option_name, _value in self.option_name2value.items():
            if _value is None:
                continue
            _value = _value.strip()

            if _value == "":
                continue
            
            # skip expression and tone
            if _option_name == "Tone" or _option_name == "Expression":
                continue

            _friendly_name = self.get_mapping_friendly_name_by_option_name(_option_name)

            if _friendly_name == "":
                continue
                
            _options_text = "%s\r\n%s: %s" % (
                _options_text, 
                _friendly_name, 
                _value
            )
        return _options_text

    def get_tone_or_expression(self):
        _tone = ""
        if "Tone" in self.option_name2value.keys():
            _tone = self.option_name2value["Tone"]
        elif "Expression" in self.option_name2value.keys():
            _tone = self.option_name2value["Expression"]
        return "" if _tone is None else _tone.strip()

    def get_mapping_friendly_name_by_option_name(self, _option_name):
        _option_name2friendly_name = {
            "ProductName": "产品名称",
            "Introduction": "产品介绍",
            "Tone": "语气",
            "Keywords": "关键词列表",
            "Information": "主题",
            "Expression": "表达方式",
            "TargetUser": "读者",
            "Characteristic": "卖点",
            "Benefits": "福利",
            "ReferenceText": "参考文本",
        }
        if _option_name not in _option_name2friendly_name.keys():
            return ""
        return _option_name2friendly_name[_option_name]