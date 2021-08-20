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
import base64

class Report(object):
    def __init__(self, stuid, password, data_path, baidu_ak, baidu_sk):
        self.stuid = stuid
        self.password = password
        self.data_path = data_path
        self.baidu_ak = baidu_ak
        self.baidu_sk = baidu_sk

    def report(self):
        loginsuccess = False
        retrycount = 5
        while (not loginsuccess) and retrycount:
            url = "https://passport.ustc.edu.cn/login?service=http%3A%2F%2Fweixine.ustc.edu.cn%2F2020%2Fcaslogin"
            session = requests.Session()

            # get CAS_LT
            response = session.get(url)
            response = BeautifulSoup(response.content, 'html.parser')
            login_form = response.find_all(class_='loginForm form-style')[0]
            CAS_LT = login_form.find_next(id='CAS_LT')['value']
            # get validate code
            vcode = self.get_vcode(session)
            data = {
                'model': 'uplogin.jsp',
                'service': 'https://weixine.ustc.edu.cn/2020/caslogin',
                'showCode': '1',
                'username': self.stuid,
                'password': str(self.password),
                'warn': '',
                'CAS_LT': CAS_LT,
                'LT': vcode,
                'button': '',
            }
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
        cookies = session.cookies
        
        with open(self.data_path, "r+") as f:
            data = f.read()
            data = json.loads(data)
            data["_token"]=token

        headers = {
            'authority': 'weixine.ustc.edu.cn',
            'origin': 'https://weixine.ustc.edu.cn',
            'upgrade-insecure-requests': '1',
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
            'referer': 'https://weixine.ustc.edu.cn/2020/home',
            'cookie': "PHPSESSID=" + cookies.get("PHPSESSID") + ";XSRF-TOKEN=" + cookies.get("XSRF-TOKEN") + ";laravel_session="+cookies.get("laravel_session"),
        }    
            
        url = "https://weixine.ustc.edu.cn/2020/daliy_report"
        print(session.post(url, data=data, headers=headers))
        data = session.get("https://weixine.ustc.edu.cn/2020").text
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

    def get_vcode(self, session):
        
        host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=' + self.baidu_ak + '&client_secret=' + self.baidu_sk
        response = requests.get(host)
        access_token = response.json()['access_token']        
        response = session.get("https://passport.ustc.edu.cn/validatecode.jsp?type=login")
        image = response.content

        request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/numbers"
        # 二进制方式打开图片文件
        # f = open('img.png', 'rb')
        img = base64.b64encode(image)

        params = {"image":img}
        # access_token = '[调用鉴权接口获取的token]'
        request_url = request_url + "?access_token=" + access_token
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        response = requests.post(request_url, data=params, headers=headers)
        vcode = response.json()['words_result'][0]['words']
        return vcode
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='URC nCov auto report script.')
    parser.add_argument('data_path', help='path to your own data used for post method', type=str)
    parser.add_argument('stuid', help='your student number', type=str)
    parser.add_argument('password', help='your CAS password', type=str)
    parser.add_argument('baidu_api_key', help='baidu api key', type=str)
    parser.add_argument('baidu_api_secret_key', help='baidu api secret key', type=str)
    
    args = parser.parse_args()

    autorepoter = Report(stuid=args.stuid, password=args.password, data_path=args.data_path, baidu_api_key=args.baidu_api_key, baidu_api_secret_key=args.baidu_api_secret_key)
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
