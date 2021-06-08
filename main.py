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
        self.course_id = course_id
        self.class_id = class_id
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

    xxt = XXT('215780498', '2567')
    xxt.set_cookie(
        'k8s=94b55a395f76dcca7b5d74ef4f49561348c0490b; route=d4fc925c8d78ce1315b0eab056f65586; uname=2004060213; lv=2; fid=1821; _uid=152804638; uf=b2d2c93beefa90dcd1ee03ad65e10855002362bacce7629380f5a15178273ea3afe9d79452e4bc0a0e3b299fbfef2254913b662843f1f4ad6d92e371d7fdf6446ece1d9f47db742bce71fc6e59483dd37d50523ec80a66bd20958d270aa2a009b95e68e0e10c56fd; _d=1623136058133; UID=152804638; vc=A36411C8D18DADE1DECFFC4CD2769FF4; vc2=929613F518C54EB32536797602C24E96; vc3=OJaL9G9LDqyUp4i28n4wmwfTLDKS2LRnRXT0TxDl44O5FKbOJiZac2ROHU1deMTOifwlVqVnAbykOfekryvgcJJvDk9rJAKIBejoa1PepIZsJrRaKkU6ZkRKx4H63dHI2un%2Fj2idzPA5TfAPESt%2Bp%2B8ufyJ2EvLfAJbfcd5oJpE%3D5618eaeea27d85ef8a52dbbf5fff3437; xxtenc=20fa5b1fdc858614416da69204450107; DSSTASH_LOG=C_38-UN_55-US_152804638-T_1623136058135; jrose=32CA1D06E5DF3F6B315D1684DF1AF20D.self-exam-system-3910617459-881q7')

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
