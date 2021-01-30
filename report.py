# encoding=utf8
import requests
import json
import time
import datetime
import pytz
import re
import sys
import argparse
from bs4 import BeautifulSoup

class Report(object):
    def __init__(self, stuid, password, data_path):
        self.stuid = stuid
        self.password = password
        self.data_path = data_path

    def report(self):
        loginsuccess = False
        retrycount = 5
        while (not loginsuccess) and retrycount:
            session = self.login()
            cookies = session.cookies
            getform = session.get("http://weixine.ustc.edu.cn/2020")
            retrycount = retrycount - 1
            if getform.url != "https://weixine.ustc.edu.cn/2020/home":
                print("Login Failed! Retry...")
            else:
                print("Login Successful!")
                loginsuccess = True
        if not loginsuccess:
            return False
        data = getform.text
        data = data.encode('ascii','ignore').decode('utf-8','ignore')
        soup = BeautifulSoup(data, 'html.parser')
        token = soup.find("input", {"name": "_token"})['value']

        with open(self.data_path, "r+") as f:
            data = f.read()
            data = json.loads(data)
            data["_token"]=token

        headers = {
            'authority': 'weixine.ustc.edu.cn',
            'path': '/2020/daliy_report',
            'scheme': 'https',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'max-age=0',
            'content-length': '312',
            'content-type': 'application/x-www-form-urlencoded',
            'cookie': '_ga=GA1.3.691870649.1576756096; experimentation_subject_id=eyJfcmFpbHMiOnsibWVzc2FnZSI6IkltRXpORGxrTkRobUxUWXhZemN0TkRVM09TMWlabUZsTFdFeU0yTXpNell4TlRrek1pST0iLCJleHAiOm51bGwsInB1ciI6ImNvb2tpZS5leHBlcmltZW50YXRpb25fc3ViamVjdF9pZCJ9fQ%3D%3D--520cc61cdaeffb0025bd7f74fc23e83860685e31; PHPSESSID=ST-e0f99993ca664407a7d4cf360e787c16; XSRF-TOKEN=eyJpdiI6IjJcL1wvTGt4dXBJS3AzK1JUNnNrUlRldz09IiwidmFsdWUiOiJsS0hOckJGN0tUZkFKQnhTZ1wvTlwvekwraVM5eGdJXC9HODhSczViVkZzTjBrYWszamFoQzltVG56ejhCcWxncVFlSGlXdlFCWk9FMllHZ1E4dFZFamlwUT09IiwibWFjIjoiYzhhZDBiYmYyZDk1NTczOWEwMDdmNmY4NDkxODI1ZWQ3NjU2NDgzNmViMzRkMGE1NGI2MDRlYTViNjVhMmQ2ZSJ9; laravel_session=eyJpdiI6IlVEckoxZnVLbVIyN3FqcUJ4dkxHUnc9PSIsInZhbHVlIjoiSzNoNWZ4Zld5TlltXC84VFlZQXA1VFFxY1RkUzVBbDJDSVVsb3k0bE8zemhjNWsrQ25vQ3VJWmtUMlM0dnlScnVMXC9QQjR4UjlNRnh6V2J5YmtRSWQwZz09IiwibWFjIjoiMjBjYWY1ODFlYzZmMjIxOGJiNmMwZWRiZjI3OGRjZTNkZDg5YjEyNjIwNDRlOTdjMDFhYjNkYmI5MmM3ZjJjNyJ9',
            'origin': 'https://weixine.ustc.edu.cn',
            'referer': 'https://weixine.ustc.edu.cn/2020/home',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
        }

        url = "http://weixine.ustc.edu.cn/2020/daliy_report"
        session.post(url, data=data)
        data = session.get("http://weixine.ustc.edu.cn/2020").text
        soup = BeautifulSoup(data, 'html.parser')
        pattern = re.compile("2021-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}")
        token = soup.find(
            "span", {"style": "position: relative; top: 5px; color: #666;"})
        print(token.text)
        flag = False
        if pattern.search(token.text) is not None:
            date = pattern.search(token.text).group()
            print("Latest report: " + date)
            date = date + " +0800"
            reporttime = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S %z")
            timenow = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
            delta = timenow - reporttime
            print("{} second(s) before.".format(delta.seconds))
            if delta.seconds < 120:
                flag = True
        if flag == False:
            print("Report FAILED!")
        else:
            print("Report SUCCESSFUL!")
        return flag

    def login(self):
        url = "https://passport.ustc.edu.cn/login?service=http%3A%2F%2Fweixine.ustc.edu.cn%2F2020%2Fcaslogin"
        data = {
            'model': 'uplogin.jsp',
            'service': 'http://weixine.ustc.edu.cn/2020/caslogin',
            'username': self.stuid,
            'password': str(self.password),
        }
        session = requests.Session()
        session.post(url, data=data)

        print("login...")
        return session


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='URC nCov auto report script.')
    parser.add_argument('data_path', help='path to your own data used for post method', type=str)
    parser.add_argument('stuid', help='your student number', type=str)
    parser.add_argument('password', help='your CAS password', type=str)
    args = parser.parse_args()
    autorepoter = Report(stuid=args.stuid, password=args.password, data_path=args.data_path)
    count = 10
    while count != 0:
        ret = autorepoter.report()
        if ret != False:
            break
        print("Report Failed, retry...")
        count = count - 1
    if count != 0:
        exit(0)
    else:
        exit(-1)
