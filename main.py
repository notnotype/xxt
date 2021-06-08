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


def get_time(length=10):
    return str(time.time()).replace('.', '')[:length]


def get_uuid():
    return str(uuid.uuid4()).replace('-', '')


class XXT:
    def __init__(self):
        self.default_headers = {
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

    def set_token(self, token: str):
        self.default_headers['authorization'] = token
        self.token = token

    def get_exam_id(self, dir_id):
        url = 'https://exm-mayuan-ans.chaoxing.com/selftest/start-test' \
              '?courseId=215779000&classId=1718&cpi=154457568&dirid={}&reset=true&protocol_v=1'.format(dir_id)
        resp = self.get(url, alive_time=999)

        # logger.debug('session headers: {!s}', spider.session.headers.__str__())
        # logger.debug('request url: {!s}', resp.response.request.url)
        # logger.debug('request headers: {!s}', resp.response.request.headers.__str__())

        result = re.search('examId=(.*?)&', resp.text, re.I)
        return result.group(1)

    def get_answer_url(self, exam_id):
        url = 'https://exm-mayuan-ans.chaoxing.com/exam/phone/look-detail' \
              '?courseId=215779000&classId=1718&examId={}&examAnswerId=301964&protocol_v=1'.format(exam_id)
        return url

    def get_question_answers(self, answer_url):
        resp = self.get(answer_url, alive_time=999)
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


if __name__ == '__main__':
    _dir_ids = [68773828, 68773829, 68773832, 68773852, 68773853, 68773855, 68773856]

    xxt = XXT()

    j_data = {'data': []}
    for _dir_id in _dir_ids:
        _exam_id = xxt.get_exam_id(_dir_id)
        logger.info("======爬取id为 [{}] 的考试======", _exam_id)
        _answer_url = xxt.get_answer_url(_exam_id)
        qa = xxt.get_question_answers(_answer_url)
        j_data['data'] += qa
        logger.info('共 {} 个items', len(j_data['data']))

    with open('out/' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.json', 'w+', encoding='utf8') as f:
        f.write(dumps(j_data))
