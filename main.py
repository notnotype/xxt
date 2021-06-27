import datetime
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

    def __init__(self, course_id=None, class_id=None):
        if course_id:
            self.course_id = course_id
        if class_id:
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

    def get_courses(self):
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
              f'?courseId={self.course_id}&classId={self.class_id}&cpi=154457568'
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

    xxt = XXT('203859054')
    xxt.set_cookie(
        'k8s=94b55a395f76dcca7b5d74ef4f49561348c0490b; route=d4fc925c8d78ce1315b0eab056f65586; source=""; cookiecheck=true; AID_dsr=55; superlib=""; msign_dsr=1624672976934; search_uuid=9e9b93bd%2d0fde%2d4478%2dbdc2%2df9986ea58bfe; mqs=19e3b526c24d63963d23bb7a0b9fd5063452ab54e90deae287793d7e4e0031dca682df1732c2ee4183fccc602da3be02be4e8fb00cc31963da0c23a6adf5ac273ff78a53bee9da7f25b21bb28f6da16c81dc0ab09bfeb6109f7e6cd7c96a142b23ab17e1b3566a10f4c7c6fc68c7adcf; rt=-2; thirdRegist=1; s=11401F839C536D9E; _industry=5; web_im_hxToken=YWMtfdhJMtZ5EeuNRrUi9FEYVaKlE4D%2d6RHksYgJxSsb8jJZFa%5fwAkMR67k%2defI%2dKewcAwMAAAF6SEeI%5fABPGgAPIftrPDHSkMUmo4PkQspYvKvFPJMbC2qprcTG3HxI3A; web_im_tid=106990444; web_im_pic=http%3a%2f%2fphoto%2echaoxing%2ecom%2fphoto%5f80%2ejpg; web_im_name=%u848b%u4fca%u6770; KI4SO_SERVER_EC=RERFSWdRQWdsckNwckxwM2pXeFFSVGJRM3E5bytLQ0NNY0U1SHBIZ250bEtGbDVZSjJybStkSXd3%0ANkprU2VsMkRtU2djWlRjU2NTVQp1NG13bWtscWxXYWJhTEMyQnlnSnFKanZDVEREdzVzN3dlclJt%0ARDFtdWE0OVd4bXBHSTZockJmNDRYdlVvNVZVdmpjVGZ2STd3VEh1Ck5EcWZVcTVkWFY1eHJCSGJM%0ARXc4NnFVTnBsbFR1T0dhMzl1cDR3V0NMYUpXOFk5bERvRG9ZODA4d002UEFoQkw1NWZMR1hYd3Rm%0AL3EKRXNpYXFmR0wrQzFVYXZZaytuamcwOGNodEJGR3IzZytOak1OQjlWRWxidWRBcXhLMHVkVkxF%0AUzNib2JiNDhLeU1RM0QweDNIc0hYSgpsYjVjbUhFeDFydEJQQUlWclZTUHJRUzh6dk1DVHBib3FS%0AU2g3WWRoOW54c2xkRndvZzNxZVhKVEFUWkZpSlRSSEhucE5nSk9sdWlwCkZLSHRVNWlsM2ExQlR5%0AaWRFVnk5dkxDYXorTCtWWUtXVG5DMU1lNDBPcDlTcmwyckxocXM2WDluVVdNTUIvTnNnZVNUP2Fw%0AcElkPTEma2V5SWQ9MQ%3D%3D; _tid=106990444; sso_puid=152804638; duxiu=userName%5fdsr%2c%3dtfm%2c%21userid%5fdsr%2c%3d23224%2c%21char%5fdsr%2c%3d%u9551%2c%21metaType%2c%3d257%2c%21dsr%5ffrom%2c%3d1%2c%21logo%5fdsr%2c%3dlogo0408%2ejpg%2c%21logosmall%5fdsr%2c%3dsmall0408%2ejpg%2c%21title%5fdsr%2c%3d%u6e56%u5357%u79d1%u6280%u5927%u5b66%2c%21url%5fdsr%2c%3d%2c%21compcode%5fdsr%2c%3d1088%2c%21province%5fdsr%2c%3d%u6e56%u5357%2c%21readDom%2c%3d%2c%21isdomain%2c%3d3%2c%21showcol%2c%3d0%2c%21hu%2c%3d0%2c%21areaid%2c%3d0%2c%21uscol%2c%3d0%2c%21isfirst%2c%3d0%2c%21istest%2c%3d0%2c%21cdb%2c%3d0%2c%21og%2c%3d0%2c%21ogvalue%2c%3d0%2c%21testornot%2c%3d1%2c%21remind%2c%3d0%2c%21datecount%2c%3d3110%2c%21userIPType%2c%3d1%2c%21my%2c%3d1%2c%21lt%2c%3d0%2c%21ttt%2c%3dfxlogin%2echaoxing%2c%21enc%5fdsr%2c%3d2AD0B126EF91D739BEBE3F62A228A1C5; spaceFid=137737; spaceRoleId=""; tl=0; jrose=44765E6CF7812D5718977CBF30450261.self-exam-system-3910617459-881q7; uname=2004060213; lv=2; fid=1821; _uid=152804638; uf=b2d2c93beefa90dcd1ee03ad65e10855002362bacce7629380f5a15178273ea3b986de932964aa04ca6bfd70c21bcc03913b662843f1f4ad6d92e371d7fdf6446ece1d9f47db742bce71fc6e59483dd37d50523ec80a66bd8d3ee8bf68b09c216f7c04307e5fa421; _d=1624776714030; UID=152804638; vc=A36411C8D18DADE1DECFFC4CD2769FF4; vc2=130C99133255AF11FB6653EF592C8DDC; vc3=N2aGp9IxQZoVUtkTvshADjyrsoSYNgCPrLrNhX%2B6w8TfyagvqAwFODhs8PDBRnOcIVnl%2Fv4jfuPlEQZtxnW%2B0ieYf3UIHFSg8k6XiKcTLV021S9fVu7Am2vxGDbejH%2BRRLRFcRIMWRZhbctqeVvBWUAfiAFtEjrn0FffvC27N5Y%3D7d9b262d0da7ea90c9923fdf72931cea; xxtenc=20fa5b1fdc858614416da69204450107; DSSTASH_LOG=C_38-UN_55-US_152804638-T_1624776714032; EXAM_FID=1821')
    xxt.get_class_id()
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

    with open('out/' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.text', 'w+', encoding='utf8') as f:
        f.write(text)
    with open('out/latest.text', 'w', encoding='utf8') as f:
        f.write(text)
