import json
import re
import logging
import datetime

import requests

from spider import Spider
from spider.spider import JsonFile

headers = {
    "Connection": 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}
cookie = {
    'Cookie': 'source=""; spaceFid=1821; spaceRoleId=""; thirdRegist=1; cookiecheck=true; duxiu=userName%5fdsr%2c%3dtfm%2c%21userid%5fdsr%2c%3d23224%2c%21char%5fdsr%2c%3d%u9551%2c%21metaType%2c%3d257%2c%21dsr%5ffrom%2c%3d1%2c%21logo%5fdsr%2c%3dlogo0408%2ejpg%2c%21logosmall%5fdsr%2c%3dsmall0408%2ejpg%2c%21title%5fdsr%2c%3d%u6e56%u5357%u79d1%u6280%u5927%u5b66%2c%21url%5fdsr%2c%3d%2c%21compcode%5fdsr%2c%3d1088%2c%21province%5fdsr%2c%3d%u6e56%u5357%2c%21readDom%2c%3d%2c%21isdomain%2c%3d3%2c%21showcol%2c%3d0%2c%21hu%2c%3d0%2c%21areaid%2c%3d0%2c%21uscol%2c%3d0%2c%21isfirst%2c%3d0%2c%21istest%2c%3d0%2c%21cdb%2c%3d0%2c%21og%2c%3d0%2c%21ogvalue%2c%3d0%2c%21testornot%2c%3d1%2c%21remind%2c%3d0%2c%21datecount%2c%3d3317%2c%21userIPType%2c%3d1%2c%21my%2c%3d1%2c%21lt%2c%3d0%2c%21ttt%2c%3dfxlogin%2echaoxing%2c%21enc%5fdsr%2c%3d9559B8AB2C2E869DF2AB4BD547B0510D; AID_dsr=55; superlib=""; msign_dsr=1606882086899; search_uuid=258fa6a8%2d370c%2d4344%2d8a98%2dbef0d5674d55; mqs=19e3b526c24d63963d23bb7a0b9fd5063452ab54e90deae287793d7e4e0031dca682df1732c2ee4183fccc602da3be02be4e8fb00cc31963c08f615ad9098e2f65de026df95a3af525b21bb28f6da16c81dc0ab09bfeb6109f7e6cd7c96a142bb27dba68c6e6aff239b06a78304fe48f; k8s=6f759bcf79168ba8d363388162b37fc521fbb43a; route=36ef5ecbfa418bb6fd1c82c50e9f0066; jrose=4358BDAA78EE50F2F5F0ED96E5B7F049.self-exam-system-514345333-9pql5; uname=2004060213; lv=2; fid=1821; _uid=152804638; uf=b2d2c93beefa90dcd1ee03ad65e10855002362bacce7629380f5a15178273ea31829dd199b39ddb7ba544dd3f351430c913b662843f1f4ad6d92e371d7fdf6446ece1d9f47db742bce71fc6e59483dd303ee8f8d5a1d15e87025d7c8109cfaac31b766465b6de9aa; _d=1606969004599; UID=152804638; vc=A36411C8D18DADE1DECFFC4CD2769FF4; vc2=678E06796F4B75439D744056BB572052; vc3=H7i8gRI6KvUA3H6ftJhnUzVBGhBJSe6mbuMisflyOGwu3goPG8TVn7TlpwXCSMOza4A5t5Ljop39UNgQBpEVUhFHfNg3bqwXB%2BIubQSf9t1MYxmOcAjWMGrRgF1LprxFObQvmkwixuQBsqrC4GDmmphf32qBVEK2ffg5%2FIm%2Bs%2Bw%3D7127b4b3527afef692f4d761ae7e7798; xxtenc=20fa5b1fdc858614416da69204450107; DSSTASH_LOG=C_38-UN_55-US_152804638-T_1606969004601',
}

spider = Spider()
logger = logging.getLogger('spider')

spider.session.cookies = requests.sessions.cookiejar_from_dict(cookie, cookiejar=None, overwrite=True)


def get_exam_id(dir_id):
    url = 'https://exm-mayuan-ans.chaoxing.com/selftest/start-test' \
          '?courseId=215779000&classId=1718&cpi=154457568&dirid={}&reset=true&protocol_v=1'.format(dir_id)
    resp = spider.get(url, cache=True)
    # logger.debug('session headers: {!s}', spider.session.headers.__str__())
    # logger.debug('request url: {!s}', resp.response.request.url)
    # logger.debug('request headers: {!s}', resp.response.request.headers.__str__())

    result = re.search('examId=(.*?)&', resp.text, re.I)
    return result.group(1)


def get_answer_url(exam_id):
    url = 'https://exm-mayuan-ans.chaoxing.com/exam/phone/look-detail' \
          '?courseId=215779000&classId=1718&examId={}&examAnswerId=301964&protocol_v=1'.format(exam_id)
    return url


def get_question_answers(answer_url):
    resp = spider.get(answer_url)
    zm_boxs = resp.xpath('//div[@class="zm_box bgColor"]')
    zr_bgs = resp.xpath('//div[@class="zr_bg"]')
    question_answers = list(zip(zm_boxs, zr_bgs))

    def elem_tostring(elem):
        elems_text_nodes = elem.xpath(".//text()")
        beautiful_text = ''.join([elem.strip() for elem in elems_text_nodes])
        return beautiful_text

    question_answers = [(elem_tostring(question), elem_tostring(answer)) for question, answer in question_answers]
    return question_answers


if __name__ == '__main__':
    _dir_ids = [68773828, 68773829, 68773832, 68773852, 68773853, 68773855, 68773856]
    f = open('out/' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.json', 'w+', encoding='utf8')
    json_file = JsonFile.from_streaming(f)
    json_file['data'] = []
    for _dir_id in _dir_ids:
        _exam_id = get_exam_id(_dir_id)
        logger.info("======爬取id为 [{}] 的考试======", _exam_id)
        _answer_url = get_answer_url(_exam_id)
        qa = get_question_answers(_answer_url)
        json_file['data'] += qa
        logger.info('共 {} 个items', len(json_file['data']))
    json_file.close()
