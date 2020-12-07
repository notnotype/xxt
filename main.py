import datetime
import logging
import re

from spider import Spider
from spider.item import JsonFile

spider = Spider()
logger = logging.getLogger('spider')

spider.set_cookie(
    'source=""; spaceFid=1821; spaceRoleId=""; thirdRegist=1; web_im_hxToken=YWMtUqmeKDfNEeu3iL%5fI%2dKxLqaKlE4D%2d6RHksYgJxSsb8jJZFa%5fwAkMR67k%2defI%2dKewcAwMAAAF2OGcymABPGgB14UM44cdnkkgjqVVQvKLOqP4Jv8hz2QwUzd%2dozfSgYA; web_im_tid=106990444; web_im_pic=http%3a%2f%2fphoto%2echaoxing%2ecom%2fphoto%5f80%2ejpg; web_im_name=%u848b%u4fca%u6770; KI4SO_SERVER_EC=RERFSWdRQWdsckNwckxwM2pXeFFSZkhPNUlCaTFuTW9NQWc4Q0U4bEdKNUtGbDVZSjJybStkSXd3%0ANkprU2VsMkRtU2djWlRjU2NTVQp1NG13bWtscWxmbmd6TEM0eE1Ed2V3NkQwMkI2T1pzN3dlclJt%0ARDFtdWE0OVd4bXBHSTZockJmNDRYdlVvNVZVdmpjVGZ2STd3VEh1Ck5EcWZVcTVkWFY1eHJCSGJM%0ARXc4NnFVTnBsbFR1T0dhMzl1cDR3V0NMYUpXOFk5bERvRG9ZODA4d002UEFoQkw1NWZMR1hYd3Rm%0AL3EKRXNpYXFmR0wrQzFVYXZZaytuamcwOGNodEJGR3IzZytOak1OQjlWRWxidWRBcXhLMHVkVkxF%0AUzNib2JiNDhLeU1RM0QweDNIc0hYSgpsYjVjbUhFeDFydEJQQUlWclZTUHJRUzh6dk1DVHBib3FS%0AU2g3WWRoOW54c2xkRndvZzNxZVhKVEFUWkZpSlRSSEhucE5nSk9sdWlwCkZLSHRVNWlsM2ExQlR5%0AaWRFVnk5dkxDYXorTCtWWUtXVG5DMU1lNDBPcDlTcmwyckxocXM2WDluVVU5Vk9UZSt1aTZLP2Fw%0AcElkPTEma2V5SWQ9MQ%3D%3D; _tid=106990444; sso_puid=152804638; _industry=5; tl=1; k8s=f373df7819ddabd293c77e2891326380f4dfde7c; jrose=F977E252A21B155355F109EA1B49E293.self-exam-system-514345333-9pql5; route=36ef5ecbfa418bb6fd1c82c50e9f0066; uname=2004060213; lv=2; fid=1821; _uid=152804638; uf=b2d2c93beefa90dcd1ee03ad65e10855002362bacce7629380f5a15178273ea377f6c5085516b692ca630d2306d8dcb8913b662843f1f4ad6d92e371d7fdf6446ece1d9f47db742bce71fc6e59483dd303ee8f8d5a1d15e82e8d43906a1adc2edee7d1bbb946cfa2; _d=1607315886979; UID=152804638; vc=A36411C8D18DADE1DECFFC4CD2769FF4; vc2=9FC97BDF629DA25DB70548939CCA5083; vc3=bAV1gUgpmyPpx8l%2BXbKg%2FNGRPQ88iN4N2EhH9JOxyubfgq2%2Fqdnk7Z9fAtpUlPML1AeEuaASSCrGu5r0EmJuqDg%2BlOLGmoE90Ec%2BwTD7zdFcayie42vihCUBWRqWjFZh1HUMpiCGOVcVWOKAULxFHcAK5zJr174VEyZQZfw3xOg%3Ddfa0d77ffa2a1f25d38e353cd3ffd14c; xxtenc=20fa5b1fdc858614416da69204450107; DSSTASH_LOG=C_38-UN_55-US_152804638-T_1607315886981')


def get_exam_id(dir_id):
    url = 'https://exm-mayuan-ans.chaoxing.com/selftest/start-test' \
          '?courseId=215779000&classId=1718&cpi=154457568&dirid={}&reset=true&protocol_v=1'.format(dir_id)
    resp = spider.get(url, alive_time=999)
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
    resp = spider.get(answer_url, alive_time=999)
    zm_boxs = resp.xpath('//div[@class="zm_box bgColor"]')
    zr_bgs = resp.xpath('//div[@class="zr_bg"]')
    question_answers = list(zip(zm_boxs, zr_bgs))

    def elem_tostring(elem):
        elms_text_nodes = elem.xpath(".//text()")
        beautiful_text = ''.join([elem.strip() for elem in elms_text_nodes])
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
