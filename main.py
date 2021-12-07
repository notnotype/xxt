import datetime
import re
import time
import uuid
from functools import wraps
from json import dumps
from typing import Dict

import requests
from loguru import logger
from lxml.etree import HTML
from requests import Session
from requests.cookies import cookiejar_from_dict


def get_time(length=10):
    return str(time.time()).replace('.', '')[:length]


def get_uuid():
    return str(uuid.uuid4()).replace('-', '')


class XXT:
    def __init__(self, course_id, class_id):
        self.course_id = 220338109
        self.class_id = 47586727
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
              f'?courseId={self.course_id}&classId={self.class_id}&cpi=154457568&dirid={dir_id}&reset=true&protocol_v=1'
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

    def get_course_ids(self):
        fid = self.client.cookies.get('fid', None)
        if not fid:
            raise RuntimeError('cookies中找不到fid， 未登录')
        url = f'https://exm-mayuan-ans.chaoxing.com/selftest/courses?fid={fid}'
        resp = self.get(url)
        resp.raise_for_status()
        html = HTML(resp.text)
        test_list = html.xpath('//ul[@class="infoList"]/li/@id')
        return test_list

    def get_test_ids(self):
        url = f'https://exm-mayuan-ans.chaoxing.com/selftest/chapter-test' \
              f'?courseId={self.course_id}&classId={self.class_id}&cpi=154457568'
        resp = self.get(url)
        resp.raise_for_status()
        html = HTML(resp.text)
        test_list = html.xpath('//div[@class="topicList"]/ul[@class="con"]/li/@id')
        return test_list



if __name__ == '__main__':
    # _dir_ids = [68773748]

    xxt = XXT('215780677', '3728')
    xxt.set_cookie(
        'lv=2; fid=1821; _uid=152804638; UID=152804638; vc=A36411C8D18DADE1DECFFC4CD2769FF4; xxtenc=20fa5b1fdc858614416da69204450107; _tid=106990444; sso_puid=152804638; _industry=5; fidsCount=3; schoolId=137737; examinationRole=cea72e64fd8ab55b9c1c500a86d45c3a; k8s=1cea45769c4c05a8f7d2682e21316a3a5973c850; route=bca6486eee9aca907e6257b7921729c3; uf=b2d2c93beefa90dcd1ee03ad65e10855002362bacce7629380f5a15178273ea3b986de932964aa04de1c393f16d8e37d913b662843f1f4ad6d92e371d7fdf6446ece1d9f47db742bce71fc6e59483dd37d50523ec80a66bd725ab6f4bfb1b6019e349e167d408b2a; _d=1624709935080; vc2=AA2FD3DBCF50E227B1319F6C4FB6A478; vc3=CSE4EdeQ4JSGgoBRBJcAp9XBVskfOmeHB9Yp0wf8pHV2AARnWEGRKsRl4mnuBleAQvlfOPloy1vldpNgGZiOs3JIZDm4Q8pK7yCkQAQz%2FjsAAQuV8Tq8wSHAjbQyFC94LXs0onD2E6EaaISO9VVc4X0Pvy8I%2Bu6gP8f7X9E%2BMEI%3D5e789164862268221875e38b4dd1a2f1; DSSTASH_LOG=C_38-UN_55-US_152804638-T_1624709935081; KI4SO_SERVER_EC=RERFSWdRQWdsckNwckxwM2pXeFFSYndFc05uVzhIR05MMWlERXJTZERXNUtGbDVZSjJybStkSXd3%0ANkprU2VsMkRtU2djWlRjU2NTVQp1NG13bWtscWxUZ3NZS2RTeGNSNDdhRWVQN05mSUVZN3dlclJt%0ARDFtdWE0OVd4bXBHSTZockJmNDRYdlVvNVZVdmpjVGZ2STd3VEh1Ck5EcWZVcTVkWFY1eHJCSGJM%0ARXc4NnFVTnBsbFR1T0dhMzl1cDR3V0NMYUpXOFk5bERvRG9ZODA4d002UEFoQkw1NWZMR1hYd3Rm%0AL3EKRXNpYXFmR0wrQzFVYXZZaytuamcwOGNodEJGR3IzZytOak1OQjlWRWxidWRBcXhLMHVkVkxF%0AUzNib2JiNDhLeU1RM0QweDNIc0hYSgpsYjVjbUhFeDFydEJQQUlWclZTUHJRUzh6dk1DVHBib3FS%0AU2g3WWRoOW54c2xkRndvZzNxZVhKVEFUWkZpSlRSSEhucE5nSk9sdWlwCkZLSHRVNWlsM2ExQlR5%0AaWRFVnk5dkxDYXorTCtWWUtXVG5DMU1lNDBPcDlTcmwyckxocXM2WDluVWNTTTRsVGYzSWRZP2Fw%0AcElkPTEma2V5SWQ9MQ%3D%3D; _dd152804638=1624709938305; jrose=66E2B5867C3D2503075F007C414E3A06.self-exam-system-3910617459-881q7; EXAM_FID=137737')
    _dir_ids = xxt.get_test_ids()
    # r = xxt.get_course_ids()
    # ic(r)
    # xxt.course_id = '215983901'
    # r = xxt.course_id = xxt.get_test_ids()
    # ic(r)

    j_data = []
    for _dir_id in _dir_ids:
        _exam_id = xxt.get_exam_id(_dir_id)
        logger.info("course_id: [{}], class_id: [{}], test_id: [{}]", xxt.course_id, xxt.class_id, _exam_id)
        _answer_url = xxt.get_answer_url(_exam_id)
        qa = xxt.get_question_answers(_answer_url)
        j_data += qa
        logger.info('共 {} 个items', len(j_data))

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
        print(question, answer)
        text += f'{question}\n{answer}\n\n'
    print(text)

    with open('out/' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.text', 'w+', encoding='utf8') as f:
        f.write(text)
    with open('out/latest.text', 'w', encoding='utf8') as f:
        f.write(text)
