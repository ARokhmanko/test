import re

class LogsParser:
    def __init__(self, logs_filename):
        self.filename = logs_filename
        self.regex_logs = re.compile("(?:\n|^)(ERROR|INFO|WARNING|ERROR) - (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\d+) - (.*) - (\d+): (.*)")
        self.refresh()

    def refresh(self):
        with open(self.filename) as f:
            self.logs_str = f.read()
        self.logs = self.regex_logs.findall(self.logs_str)
        self.logs = [{n:f for n, f in zip(["type", "datetime", "chat_id", "sender", "sender_id", "text"], l)} for l in self.logs]
        self.logs = [l for l in self.logs if l["type"]=="INFO"]

    def get(self, chat_id=None, max_len=None):
        self.refresh()
        logs = [l for l in self.logs if l["chat_id"]==str(chat_id)] if chat_id else self.logs
        return logs[-max_len:] if max_len else logs

    def get_text(self, chat_id=None, max_len=None, tech=False):
        logs = self.get(chat_id=chat_id, max_len=max_len)
        pointer = '✍️ '
        if tech:
            tlogs = ["*{}, {} {}*: {}".format(l["datetime"].split(',')[0], l["sender"], l["sender_id"], l["text"]) for l in logs]
        else:
            tlogs = ["*{}, {}*: {}".format(l["datetime"].split(',')[0], l["sender"], l["text"]) for l in logs]
        res = pointer + ('\n'+pointer).join(tlogs)
        if res==pointer:
            return ''
        else:
            return res

if __name__ == "__main__":
    logs = LogsParser("../workdata/hist.log")
    print("total len: %d" % len(logs.logs))
    print(logs.get_text(max_len=10, tech=True))
