import datetime
import os
import re
import time
import uuid
from functools import wraps
from json import dumps
from typing import Dict

import requests
from icecream import ic
from loguru import logger
from lxml.etree import HTML
from requests import Session
from requests.cookies import cookiejar_from_dict


def get_time(length=10):
    return str(time.time()).replace('.', '')[:length]


def get_uuid():
    return str(uuid.uuid4()).replace('-', '')


class XXT:
    course_id: str
    class_id: str
    cpi: str

    def __init__(self, course_id=None, class_id=None, cpi=None):
        if course_id:
            self.course_id = course_id
        if class_id:
            self.class_id = class_id
        if cpi:
            self.cpi = cpi
        self.default_headers = {
            'Host': 'exm-mayuan-ans.chaoxing.com',
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

    def get_exam_id(self, dir_id):
        url = 'https://exm-mayuan-ans.chaoxing.com/selftest/start-test' \
              f'?courseId={self.course_id}&classId={self.class_id}&cpi={self.cpi}&dirid={dir_id}&reset=true&protocol_v=1'
        resp = self.get(url)

        # logger.debug('session headers: {!s}', self.client.headers.__str__())
        # logger.debug('request url: {!s}', resp.request.url)
        # logger.debug('request url: {!s}', resp.history[0].url)
        # logger.debug('request headers: {!s}', resp.request.headers.__str__())

        result = re.search('examId=(.*?)&', resp.text, re.I)
        # print(resp.text)
        return result.group(1)

    def get_answer_url(self, exam_id):
        url = 'https://exm-mayuan-ans.chaoxing.com/exam/phone/look-detail' \
              f'?courseId={self.course_id}&classId={self.class_id}&examId={exam_id}&examAnswerId=301964&protocol_v=1'
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

    def get_courses(self):
        # new api https://mobile3.chaoxing.com/newmobile/getUserApps?fid=137737&isMergerMks=true&uid=109255777
        fid = self.client.cookies.get('fid', None)
        if not fid:
            raise RuntimeError('cookies中找不到fid， 未登录')
        url = f'https://exm-mayuan-ans.chaoxing.com/selftest/courses?fid={fid}'
        resp = self.get(url)
        resp.raise_for_status()
        html = HTML(resp.text)
        course_list = html.xpath('//ul[@class="infoList"]/li/@id')
        course_title = html.xpath('//ul[@class="infoList"]/li/div/p/span/text()')
        return list(zip(course_list, course_title))

    def get_test_ids(self):
        url = f'https://exm-mayuan-ans.chaoxing.com/selftest/chapter-test' \
              f'?courseId={self.course_id}&classId={self.class_id}&cpi={self.cpi}'
        resp = self.get(url)
        resp.raise_for_status()
        html = HTML(resp.text)
        test_list = html.xpath('//div[@class="topicList"]/ul[@class="con"]/li/@id')
        return test_list

    def get_class_id(self):
        url = f'https://exm-mayuan-ans.chaoxing.com/selftest/mode?courseId={self.course_id}'
        resp = self.get(url)
        resp.raise_for_status()
        html = HTML(resp.text)
        self.class_id = html.xpath('//input[@name="classId"]/@value')[0]
        return self.class_id


if __name__ == '__main__':
    # _dir_ids = [68773748]

    # xxt = XXT('215780579', '2546', '98652693')
    xxt = XXT('221775430', '5952', '154457568')  # 毛泽东思想和中国特色社会主义理论体系概论
    xxt.set_cookie('source=""; lv=2; fid=1821; _uid=152804638; uf=b2d2c93beefa90dcd1ee03ad65e10855002362bacce7629380f5a15178273ea351003e8a2ec1803d71dd6991d88d6874913b662843f1f4ad6d92e371d7fdf6446ece1d9f47db742bce71fc6e59483dd37a48b563e48d11a1969a3093fc9ab8cd284ae521b46d3af3; _d=1655441189645; UID=152804638; vc=A36411C8D18DADE1DECFFC4CD2769FF4; vc2=E2E094C63B595E0E1DF3ADEFA689E679; vc3=FtAWe8ZX8VEJ%2FyxG6NFtj8QLUDrStroFXokiDT93PQ%2Fj%2BfF2dTAAd%2F9Bi3zcgakwajpT03HKOC7uruidUiy4DR3Q3Pa9D7S0%2BAlxntB9m4UePtRWr7Mun6905I0mej2pm17NOHtIQhBRD6mWJvGtECqDY5U9qbcy6zm0%2BYwfd%2F8%3D75b711830e07d638d597e7877c323cf6; xxtenc=de8eca84b06e70aa09b24f2cc43d95b2; DSSTASH_LOG=C_38-UN_55-US_152804638-T_1655441189647; spaceFid=1821; spaceRoleId=""; k8s=a9842f22e858ecaaffe41d3449c642650d234086; jrose=9B64C1FE8E6B6324B467DDF1AEE0649B.self-exam-system-2964081028-01ch8; EXAM_FID=137737; route=ce3aca120f3fcc9eb76807ea1ee5aae1')
    # xxt.get_class_id()
    _dir_ids = xxt.get_test_ids()

    r = xxt.get_courses()
    ic(r)

    j_data = []
    for _dir_id in _dir_ids:
        _exam_id = xxt.get_exam_id(_dir_id)
        logger.info("course_id: [{}], class_id: [{}], test_id: [{}]", xxt.course_id, xxt.class_id, _exam_id)
        _answer_url = xxt.get_answer_url(_exam_id)
        qa = xxt.get_question_answers(_answer_url)
        j_data += qa
        logger.info('共 {} 个items', len(j_data))

    if not os.path.exists("out/"):
        os.mkdir("out")
    with open('out/' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.json', 'w+', encoding='utf8') as f:
        f.write(dumps(j_data, indent=4, ensure_ascii=False))
    with open('out/latest.json', 'w', encoding='utf8') as f:
        f.write(dumps(j_data, indent=4, ensure_ascii=False))

    text = ''
    for each in j_data:
        question, answer = each
        question = re.subn('([a-zA-Z]).', '\n\g<1>: ', question)[0]
        question = re.subn('[0-9]*、', '', question)[0]
        # answer = answer.replace('正确答案：', '')
        answer = answer.replace('正确答案：', '正确答案: ')
        answer = answer.replace('我的答案：', '')
        # print(question, answer)
        text += f'{question}\n{answer}\n\n'
    # print(text)

    with open('out/' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.txt', 'w+', encoding='utf8') as f:
        f.write(text)
    with open('out/latest.txt', 'w', encoding='utf8') as f:
        f.write(text)
