import datetime
import os
import re
import time
import uuid
from functools import wraps
from json import dumps
from typing import Dict
import loguru

import requests
from icecream import ic
from loguru import logger
from lxml.etree import HTML
from requests import Session, HTTPError
from requests.cookies import cookiejar_from_dict
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad
from icecream import ic

RED = '\033[31m'
BLUE = '\033[34m'
GREEN = '\033[32m'
RESET = '\033[0m'


def get_time(length=10):
    return str(time.time()).replace('.', '')[:length]


def get_uuid():
    return str(uuid.uuid4()).replace('-', '')


class XXT:

    def __init__(self):
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36'
        }
        self.client = Session()
        self.proxies = {}

    def set_proxies(self, proxies: Dict):
        self.proxies = proxies

    @wraps(requests.get)
    def get(self, url, **kwargs):
        temp_headers = self.default_headers.copy()
        temp_headers.update(kwargs['headers'] if 'headers' in kwargs else {})
        kwargs['headers'] = temp_headers
        kwargs.setdefault('proxies', self.proxies)
        return self.client.get(url, **kwargs)

    @wraps(requests.post)
    def post(self, url, **kwargs):
        temp_headers = self.default_headers.copy()
        temp_headers.update(kwargs['headers'] if 'headers' in kwargs else {})
        kwargs['headers'] = temp_headers
        kwargs.setdefault('proxies', self.proxies)
        return self.client.post(url, **kwargs)

    def set_cookie(self, cookies: str):
        cookies_dict = {}
        for cookie in cookies.strip().split(';'):
            k, v = cookie.strip().split('=')
            cookies_dict[k.strip()] = v.strip()
        self.default_headers['Cookie'] = cookies
        self.client.cookies = cookiejar_from_dict(cookies_dict, self.client.cookies, True)

    def get_exam_id(self, course_id, class_id, cpi, dir_id):
        url = 'https://exm-mayuan-ans.chaoxing.com/selftest/start-test' \
              f'?courseId={course_id}&classId={class_id}&cpi={cpi}&dirid={dir_id}&reset=true&protocol_v=1'
        resp = self.get(url)
        result = re.search('examId=(.*?)&', resp.text, re.I)
        return result.group(1)

    def get_answer_url(self, course_id, class_id, cpi, exam_id):
        url = 'https://exm-mayuan-ans.chaoxing.com/exam/phone/look-detail' \
              f'?courseId={course_id}&classId={class_id}&examId={exam_id}&examAnswerId=301964&protocol_v=1'
        return url

    def get_question_answers(self, answer_url):
        resp = self.get(answer_url)
        html = HTML(resp.text)
        zm_boxs = html.xpath('//div[@class="zm_box bgColor"]')
        zr_bgs = html.xpath('//div[@class="zr_bg"]')
        question_answers = list(zip(zm_boxs, zr_bgs))

        def elem_tostring(elem):
            elms_text_nodes = elem.xpath(".//text()")
            beautiful_text = ''.join([elem.strip() for elem in elms_text_nodes])
            return beautiful_text

        question_answers = [(elem_tostring(question), elem_tostring(answer)) for question, answer in question_answers]
        return question_answers

    def get_courses(self, fid=None):
        # new api https://mobile3.chaoxing.com/newmobile/getUserApps?fid=137737&isMergerMks=true&uid=109255777
        fid = fid or self.client.cookies.get('fid', None)
        if not fid:
            raise RuntimeError('cookies中找不到fid， 未登录')
        url = f'https://exm-mayuan-ans.chaoxing.com/selftest/courses?fid={fid}'
        resp = self.get(url)
        resp.raise_for_status()
        html = HTML(resp.text)
        course_list = html.xpath('//ul[@class="infoList"]/li/@id')
        course_title = html.xpath('//ul[@class="infoList"]/li/div/p/span/text()')
        return list(zip(course_list, course_title))

    def get_test_ids(self, course_id, class_id, cpi):
        url = f'https://exm-mayuan-ans.chaoxing.com/selftest/chapter-test' \
              f'?courseId={course_id}&classId={class_id}&cpi={cpi}'
        resp = self.get(url)
        resp.raise_for_status()
        html = HTML(resp.text)
        test_list = html.xpath('//div[@class="topicList"]/ul[@class="con"]/li/@id')
        return test_list
    
    def login(self, username, password):
        def encrypt(text):
            key = b'u2oh6Vu^'
            pad_pkcs7 = pad(text.encode(), DES.block_size, style='pkcs7')
            des = DES.new(key, DES.MODE_ECB)
            return des.encrypt(pad_pkcs7).hex()
        api = f'http://passport2.chaoxing.com/fanyalogin'
        data = {
            'fid': '-1',
            'uname': username,
            'password': encrypt(password),
            'refer': 'http%3A%2F%2Fi.chaoxing.com',
            't': 'true',
            'forbidotherlogin': '0',
            'validate': None,
        }
        resp = self.post(api, data=data)
        resp.raise_for_status()
        logger.debug(resp.json())
        cookies = ''
        for k, v in self.client.cookies.get_dict().items():
            cookies += f'{k}={v}; '
        return cookies

    def get_schools(self):
        api = 'http://i.chaoxing.com/base/cacheUserOrg'
        resp = self.get(api)
        resp.raise_for_status()
        result = []
        for each in resp.json()['site']:
            result.append((each['fid'], each['schoolname']))
        return result
    
    def crawl_course(self, course_id):
        courses = xxt.get_schools()
        course_name = 'unknown_course'
        for school_id, school_name in courses:
                for _course_id, _course_name in xxt.get_courses(school_id):
                    if _course_id == course_id:
                        course_name = _course_name[:10]

        api = f'https://exm-mayuan-ans.chaoxing.com/selftest/mode?courseId={course_id}'
        resp = self.get(api)
        resp.raise_for_status()
        html = HTML(resp.text)

        class_id = html.xpath('//input[@name="classId"]/@value')[0]
        cpi = html.xpath('//input[@name="cpi"]/@value')[0]

        _dir_ids = self.get_test_ids(course_id, class_id, cpi, )

        j_data = []
        for _dir_id in _dir_ids:
            _exam_id = self.get_exam_id(course_id, class_id, cpi, _dir_id)
            logger.info("course_id: [{}], class_id: [{}], test_id: [{}]", course_id, class_id, _exam_id)
            _answer_url = self.get_answer_url(course_id, class_id, cpi, _exam_id)
            qa = self.get_question_answers(_answer_url)
            j_data += qa
            logger.info('共 {} 个items', len(j_data))

        now_str = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M')

        if not os.path.exists("out/"):
            os.mkdir("out")
        with open(f'out/{course_name}({course_id})-{now_str}.json', mode='w', encoding='utf8') as f:
            f.write(dumps(j_data, indent=4, ensure_ascii=False))
        with open(f'out/{course_name}({course_id})-latest.json', mode='w', encoding='utf8') as f:
            f.write(dumps(j_data, indent=4, ensure_ascii=False))

        text = ''
        for each in j_data:
            question, answer = each
            question = re.subn('([a-zA-Z]).', '\n\g<1>: ', question)[0]
            question = re.subn('[0-9]*、', '', question)[0]
            answer = answer.replace('正确答案：', '正确答案: ')
            answer = answer.replace('我的答案：', '')
            text += f'{question}\n{answer}\n\n'

        with open(f'out/{course_name}({course_id})-{now_str}.txt', mode='w', encoding='utf8') as f:
            f.write(text)
        with open(f'out/{course_name}({course_id})-latest.txt', mode='w', encoding='utf8') as f:
            f.write(text)

if __name__ == '__main__':
    username = input('输入手机号: ')
    password = input('输入密码: ')
    xxt = XXT()
    xxt.login(username, password)
    
    courses = xxt.get_schools()
    for school_id, school_name in courses:
        print(f'{GREEN}{school_name} (school_id: {BLUE}{school_id}){RESET}')
        for course_id, course_name in xxt.get_courses(school_id):
            print(f'    {GREEN}{course_name} (course_id: {BLUE}{course_id}){RESET}')
    xxt.crawl_course(input('请输入课程id(course_id): '))

    
