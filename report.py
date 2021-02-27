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
            url = "https://passport.ustc.edu.cn/login"
            data = {
                'model': 'uplogin.jsp',
                'service': 'https://weixine.ustc.edu.cn/2020/caslogin',
                'showCode': '',
                'username': self.stuid,
                'password': str(self.password)
            }
            session = requests.Session()
            r = session.post(url, data=data)
            print("login...")
            retrycount = retrycount - 1
            if r.url != "https://weixine.ustc.edu.cn/2020/home":
                print(r.url)
                print("Login Failed! Retry...")
            else:
                print("Login Successful!")
                loginsuccess = True
        if not loginsuccess:
            return False
        data = r.text
        data = data.encode('ascii','ignore').decode('utf-8','ignore')
        soup = BeautifulSoup(data, 'html.parser')
        token = soup.find("input", {"name": "_token"})['value']

        with open(self.data_path, "r+") as f:
            data = f.read()
            data = json.loads(data)
            data["_token"]=token

        url = "http://weixine.ustc.edu.cn/2020/daliy_report"
        session.post(url, data=data)
        data = session.get("http://weixine.ustc.edu.cn/2020").text
        soup = BeautifulSoup(data, 'html.parser')
        pattern = re.compile("2021-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}")
        token = soup.find(
            "span", {"style": "position: relative; top: 5px; color: #666;"})
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

        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='URC nCov auto report script.')
    parser.add_argument('data_path', help='path to your own data used for post method', type=str)
    parser.add_argument('stuid', help='your student number', type=str)
    parser.add_argument('password', help='your CAS password', type=str)
    args = parser.parse_args()
    autorepoter = Report(stuid=args.stuid, password=args.password, data_path=args.data_path)
    count = 5
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
