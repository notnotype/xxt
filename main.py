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

    xxt = XXT('215780579', '2546', '98652693')
    xxt.set_cookie(
        '_tid=76653558; sso_puid=109255777; _industry=5; fidsCount=3; k8s=bd0734ff408fe052a7df7557586b72e1a4822de8; route=36ef5ecbfa418bb6fd1c82c50e9f0066; schoolId=28948; examinationRole=8930d67295f8174b1469b2760b06a181; lv=2; fid=28948; _uid=109255777; UID=109255777; vc=43D57B2F0862A3BE50B0A7D5A7EF36F7; xxtenc=7cec5c59032021221fac4a42fb2f685b; jrose=BC228CCB7C7BD719F2E4822DF066CECB.self-exam-system-3661515132-4k7t2; uf=da0883eb5260151ed8722d802b2f755939c33fa9270a6a53cb316d38e6bde71a10c1943b3809c41e04f68592bfcd5b39dc436c455fddffc288b83130e7eb47045be6cb53ca92c59efd68be96b6183b1a7a5853460b99e4b1e71de711cfced6a4cbb59410137500e5; _d=1640838192883; vc2=0E6DD14E13562548AAB5DF0F0DEAA16C; vc3=a3BPmh3MNOPr5WnuovoymGQY9Zbgt6CqPMAIY56krplZfarL%2BXScJGdp6hctnsZw8sIRLqDE7s6O616LinbUUT6KuGvAkiCJBLdnzQjEIziQSGwAxYlV6q0TvMWbhW0L%2BnyXEnOZ%2FfkfGytW47%2FWsfOy8wpUrj6%2Bz7y0MM2NKmo%3Da3b8e0b9d91027fdae83fd3c3583867c; DSSTASH_LOG=C_38-UN_55-US_109255777-T_1640838192885; KI4SO_SERVER_EC=RERFSWdRQWdsckNwckxwM2pXeFFSYm56cm9PN0FsM0pxNlJDVHAwY0VEVEFlcGQ0ZzI0MDJ1MHd4%0AQUZDOXpKeERtU2djWlRjU2NTVQp1NG13bWtscWxXdHBSbWxzZ0RXMEsvcy9TR0FMVHlBN3dlclJt%0ARDFtdWE0OVd4bXBHSTZobzIwWGJJR3JZd3B1cGJ0Zmdqd0ZqRWxPCjhKbkRyZHlUMEZ6WTZTRkxz%0AYmo4cjhzaFI5NncrdUdhMzl1cDR3V0NMYUpXOFk5bERvRG9ZODA4d002UEFoQkw1NWZMR1hYd3Rm%0AL3EKRXNpYXFmR0wrQzFVYXZZaytuamcwOGNodEJGR3IzZytOak1OQjlWRWxidWRBcXhLMHVkVkxF%0AUzNib2JiNDhLeU1RM0QweDFZRjkxMwpLTGRvZVpzQm9Kbis2Y3p2RVlEaU5ndnM0aHJqd3JJeERj%0AUFRIWXo3bi9oazJ0cm4zMmx1ZDJMSXkyK0pCRUFOSExFbndPUENzakVOCnc5TWRXQmZkZHlpM2FI%0AbjJGNzVlK2RHZW1ub3dVUVVJYWRoZXJJdVJhVUp6bjVycU5SYzlCa3U2blFuMDh2VEgzbHJuP2Fw%0AcElkPTEma2V5SWQ9MQ%3D%3D; EXAM_FID=137737')
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
        print(question, answer)
        text += f'{question}\n{answer}\n\n'
    print(text)

    with open('out/' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.text', 'w+', encoding='utf8') as f:
        f.write(text)
    with open('out/latest.text', 'w', encoding='utf8') as f:
        f.write(text)
