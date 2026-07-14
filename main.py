import argparse
import datetime
import getpass
import re
import time
import uuid
from dataclasses import dataclass, field
from functools import wraps
from json import dumps
from pathlib import Path
from typing import Dict
from urllib.parse import urlencode

import requests
from loguru import logger
from lxml.etree import HTML
from requests import Session
from requests.cookies import cookiejar_from_dict
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad

RED = '\033[31m'
BLUE = '\033[34m'
GREEN = '\033[32m'
RESET = '\033[0m'


@dataclass
class Question:
    """A single question extracted from a self-test answer page."""

    number: int
    stem: str
    answer: str = ''
    status: str = 'parsed'
    options: dict[str, str] = field(default_factory=dict)


@dataclass
class ParseReport:
    """Extraction result, including data that could not be parsed safely."""

    questions: list[Question]
    diagnostics: list[str] = field(default_factory=list)

    @property
    def source_question_count(self) -> int:
        return len(self.questions)

    @property
    def parsed_question_count(self) -> int:
        return sum(question.status == 'parsed' for question in self.questions)


@dataclass
class CrawlReport:
    """The observable outcome of one course export."""

    course_id: str
    course_name: str
    questions: list[Question]
    diagnostics: list[str] = field(default_factory=list)
    output_files: list[Path] = field(default_factory=list)

    @property
    def total_questions(self) -> int:
        return len(self.questions)

    @property
    def complete_questions(self) -> int:
        return sum(question.status == 'parsed' for question in self.questions)

    @property
    def incomplete_questions(self) -> int:
        return self.total_questions - self.complete_questions


class QuestionParser:
    """Parse a result page without silently discarding unmatched questions."""

    QUESTION_XPATH = ('//div[contains(concat(" ", normalize-space(@class), " "), " zm_box ") '
                      'and contains(concat(" ", normalize-space(@class), " "), " bgColor ")]')
    ANSWER_XPATH = '//div[contains(concat(" ", normalize-space(@class), " "), " zr_bg ")]'

    @staticmethod
    def _text(element) -> str:
        return ''.join(text.strip() for text in element.xpath('.//text()') if text.strip())

    @staticmethod
    def _split_options(text: str) -> tuple[str, dict[str, str]]:
        matches = list(re.finditer(r'(?<![A-Za-z])([A-F])\s*[.、:：]\s*', text))
        if not matches:
            return text, {}
        options = {}
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            options[match.group(1)] = text[match.end():end].strip()
        return text[:matches[0].start()].strip(), options

    def parse(self, page: str) -> ParseReport:
        html = HTML(page)
        question_nodes = html.xpath(self.QUESTION_XPATH)
        answer_nodes = html.xpath(self.ANSWER_XPATH)
        questions: list[Question] = []
        diagnostics: list[str] = []
        answer_mapping_is_reliable = len(question_nodes) == len(answer_nodes)

        if question_nodes and not answer_mapping_is_reliable:
            diagnostics.append(
                f'题目节点数为 {len(question_nodes)}，答案节点数为 {len(answer_nodes)}；答案对应关系不可靠'
            )

        for index, question_node in enumerate(question_nodes, start=1):
            stem, options = self._split_options(self._text(question_node))
            if answer_mapping_is_reliable:
                answer = self._text(answer_nodes[index - 1])
                status = 'parsed' if answer else 'missing_answer'
                if not answer:
                    diagnostics.append(f'第 {index} 题的答案节点为空')
            else:
                answer = self._text(answer_nodes[index - 1]) if index <= len(answer_nodes) else ''
                status = 'ambiguous_answer_mapping'
            questions.append(Question(index, stem, answer, status, options))

        if len(answer_nodes) > len(question_nodes):
            diagnostics.append(
                f'检测到 {len(answer_nodes) - len(question_nodes)} 个无法匹配题目的答案节点'
            )
        if not question_nodes:
            diagnostics.append('未识别到题目节点；页面结构可能已变更或该课程没有可查看的题目')
        return ParseReport(questions, diagnostics)


class XXTError(RuntimeError):
    """Base error for failures a command-line user can act on."""


class CourseUnavailableError(XXTError):
    """The selected course does not expose a compatible self-test page."""


class LoginError(XXTError):
    """Authentication failed or returned an unsupported response."""


class SessionExpiredError(XXTError):
    """A request requires a fresh authenticated session."""


class ExportError(XXTError):
    """An export configuration or file cannot be produced."""


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
        self.timeout = 15
        self._exam_answer_ids = {}

    def set_proxies(self, proxies: Dict):
        self.proxies = proxies

    @wraps(requests.get)
    def get(self, url, **kwargs):
        temp_headers = self.default_headers.copy()
        temp_headers.update(kwargs['headers'] if 'headers' in kwargs else {})
        kwargs['headers'] = temp_headers
        kwargs.setdefault('proxies', self.proxies)
        kwargs.setdefault('timeout', self.timeout)
        return self.client.get(url, **kwargs)

    @wraps(requests.post)
    def post(self, url, **kwargs):
        temp_headers = self.default_headers.copy()
        temp_headers.update(kwargs['headers'] if 'headers' in kwargs else {})
        kwargs['headers'] = temp_headers
        kwargs.setdefault('proxies', self.proxies)
        kwargs.setdefault('timeout', self.timeout)
        return self.client.post(url, **kwargs)

    def set_cookie(self, cookies: str):
        cookies_dict = {}
        for cookie in cookies.strip().split(';'):
            if not cookie.strip() or '=' not in cookie:
                continue
            k, v = cookie.strip().split('=', 1)
            if not k:
                continue
            cookies_dict[k.strip()] = v.strip()
        self.default_headers['Cookie'] = cookies
        self.client.cookies = cookiejar_from_dict(cookies_dict, self.client.cookies, True)

    def get_exam_id(self, course_id, class_id, cpi, dir_id):
        url = 'https://exm-mayuan-ans.chaoxing.com/selftest/start-test' \
              f'?courseId={course_id}&classId={class_id}&cpi={cpi}&dirid={dir_id}&reset=true&protocol_v=1'
        resp = self.get(url)
        resp.raise_for_status()
        result = re.search('examId=(.*?)&', resp.text, re.I)
        if not result:
            raise CourseUnavailableError(
                f'自测目录 {dir_id} 未返回 examId；题目可能不可用或页面结构已变更'
            )
        exam_id = result.group(1)
        answer_result = re.search(r'examAnswerId=([^&"\'\s]+)', resp.text, re.I)
        if answer_result:
            self._exam_answer_ids[exam_id] = answer_result.group(1)
        return exam_id

    def get_answer_url(self, course_id, class_id, cpi, exam_id):
        answer_id = self._exam_answer_ids.get(exam_id, '301964')
        query = urlencode({
            'courseId': course_id,
            'classId': class_id,
            'examId': exam_id,
            'examAnswerId': answer_id,
            'protocol_v': 1,
        })
        return f'https://exm-mayuan-ans.chaoxing.com/exam/phone/look-detail?{query}'

    def get_question_report(self, answer_url):
        resp = self.get(answer_url)
        resp.raise_for_status()
        report = QuestionParser().parse(resp.text)
        for diagnostic in report.diagnostics:
            logger.warning(diagnostic)
        return report

    def get_question_answers(self, answer_url):
        """Backward-compatible tuple view of :meth:`get_question_report`."""
        report = self.get_question_report(answer_url)
        return [(question.stem, question.answer) for question in report.questions]

    def get_courses(self, fid=None):
        # new api https://mobile3.chaoxing.com/newmobile/getUserApps?fid=137737&isMergerMks=true&uid=109255777
        fid = fid or self.client.cookies.get('fid', None)
        if not fid:
            raise SessionExpiredError('登录状态已失效（Cookie 中缺少 fid），请重新登录')
        url = f'https://exm-mayuan-ans.chaoxing.com/selftest/courses?fid={fid}'
        resp = self.get(url)
        resp.raise_for_status()
        html = HTML(resp.text)
        course_list = html.xpath('//ul[@class="infoList"]/li/@id')
        course_title = html.xpath('//ul[@class="infoList"]/li/div/p/span/text()')
        return list(zip(course_list, course_title))

    def resolve_course_parameters(self, course_id, class_id=None, cpi=None):
        """Return the self-test parameters or explain why the course cannot run.

        Supplying both optional parameters is an explicit recovery path for a
        compatible page whose hidden fields are unavailable to the parser.
        """
        if bool(class_id) != bool(cpi):
            raise ValueError('classId 和 cpi 必须同时提供')
        if class_id and cpi:
            return str(class_id), str(cpi)

        api = f'https://exm-mayuan-ans.chaoxing.com/selftest/mode?courseId={course_id}'
        resp = self.get(api)
        resp.raise_for_status()
        html = HTML(resp.text)
        class_ids = html.xpath('//input[@name="classId"]/@value')
        cpis = html.xpath('//input[@name="cpi"]/@value')
        if not class_ids or not cpis:
            page_text = ''.join(html.xpath('//text()')).strip()
            detail = f' 页面提示：{page_text[:120]}' if page_text else ''
            raise CourseUnavailableError(
                f'课程 {course_id} 未提供自测参数（classId/cpi）。'
                f'该课程可能未开通自测或页面结构已变更。{detail}'
            )
        return class_ids[0], cpis[0]

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
        api = 'https://passport2.chaoxing.com/fanyalogin'
        data = {
            'fid': '-1',
            'uname': username,
            'password': encrypt(password),
            'refer': 'https%3A%2F%2Fi.chaoxing.com',
            't': 'true',
            'forbidotherlogin': '0',
            'validate': None,
        }
        resp = self.post(api, data=data)
        resp.raise_for_status()
        try:
            result = resp.json()
        except ValueError as error:
            raise LoginError('登录接口未返回有效数据，请稍后重试或更新登录地址') from error
        if not isinstance(result, dict):
            raise LoginError('登录接口返回了未知数据格式，请稍后重试或更新程序')
        logger.debug('登录接口返回 status={}', bool(result.get('status')))
        if not result.get('status'):
            raise LoginError(result.get('msg2') or result.get('mes') or '登录失败')
        cookies = ''
        for k, v in self.client.cookies.get_dict().items():
            cookies += f'{k}={v}; '
        return cookies

    def get_schools(self):
        api = 'https://i.chaoxing.com/base/cacheUserOrg'
        resp = self.get(api)
        resp.raise_for_status()
        try:
            payload = resp.json()
        except ValueError as error:
            raise SessionExpiredError('登录状态已失效或学校列表接口返回了非 JSON 数据，请重新登录') from error
        if not isinstance(payload.get('site'), list):
            raise SessionExpiredError('登录状态已失效，无法获取学校列表，请重新登录后重试')
        result = []
        for each in payload['site']:
            if not isinstance(each, dict) or not each.get('fid') or not each.get('schoolname'):
                continue
            result.append((each['fid'], each['schoolname']))
        return result
    
    @staticmethod
    def _safe_filename(value: str) -> str:
        return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', value).strip() or 'unknown_course'

    def _write_exports(self, report: CrawlReport, output_dir, formats):
        supported_formats = {'json', 'txt', 'xlsx'}
        formats = {item.lower() for item in formats}
        unsupported = formats - supported_formats
        if unsupported:
            raise ExportError(f'不支持的导出格式：{", ".join(sorted(unsupported))}')
        if not formats:
            raise ExportError('至少需要一种导出格式')

        directory = Path(output_dir)
        directory.mkdir(parents=True, exist_ok=True)
        name = self._safe_filename(report.course_name)[:80]
        prefix = f'{name}({self._safe_filename(report.course_id)})'
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
        records = [
            {
                'number': question.number,
                'question': question.stem,
                'options': question.options,
                'answer': question.answer,
                'status': question.status,
            }
            for question in report.questions
        ]

        if 'json' in formats:
            for suffix in (f'{prefix}-{timestamp}.json', f'{prefix}-latest.json'):
                path = directory / suffix
                path.write_text(dumps(records, indent=4, ensure_ascii=False), encoding='utf8')
                report.output_files.append(path)

        if 'txt' in formats:
            text = ''
            for question in report.questions:
                stem = re.sub(r'([a-zA-Z])\.', r'\n\1: ', question.stem)
                stem = re.sub(r'[0-9]*、', '', stem)
                answer = question.answer.replace('正确答案：', '正确答案: ').replace('我的答案：', '')
                if question.status != 'parsed':
                    answer = f'[解析状态: {question.status}] {answer}'.strip()
                text += f'{stem}\n{answer}\n\n'
            for suffix in (f'{prefix}-{timestamp}.txt', f'{prefix}-latest.txt'):
                path = directory / suffix
                path.write_text(text, encoding='utf8')
                report.output_files.append(path)

        if 'xlsx' in formats:
            try:
                from openpyxl import Workbook
            except ImportError as error:
                raise ExportError('导出 XLSX 需要安装 openpyxl，请执行 pip install -r requirements.txt') from error
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = '题库'
            sheet.append(['题号', '题目', 'A', 'B', 'C', 'D', 'E', 'F', '答案', '解析状态'])
            for row in records:
                sheet.append([
                    row['number'], row['question'],
                    *(row['options'].get(option) for option in ('A', 'B', 'C', 'D', 'E', 'F')),
                    row['answer'], row['status'],
                ])
            for column, width in {
                'A': 8, 'B': 45, 'C': 25, 'D': 25, 'E': 25, 'F': 25,
                'G': 25, 'H': 25, 'I': 35, 'J': 18,
            }.items():
                sheet.column_dimensions[column].width = width
            for suffix in (f'{prefix}-{timestamp}.xlsx', f'{prefix}-latest.xlsx'):
                path = directory / suffix
                workbook.save(path)
                report.output_files.append(path)

    def crawl_course(self, course_id, class_id=None, cpi=None, output_dir='out', formats=('json', 'txt')):
        course_name = 'unknown_course'
        if not (class_id and cpi):
            for school_id, _school_name in self.get_schools():
                for _course_id, _course_name in self.get_courses(school_id):
                    if _course_id == course_id:
                        course_name = _course_name

        class_id, cpi = self.resolve_course_parameters(course_id, class_id, cpi)

        _dir_ids = self.get_test_ids(course_id, class_id, cpi, )

        questions = []
        diagnostics = []
        for _dir_id in _dir_ids:
            _exam_id = self.get_exam_id(course_id, class_id, cpi, _dir_id)
            logger.info("course_id: [{}], class_id: [{}], test_id: [{}]", course_id, class_id, _exam_id)
            _answer_url = self.get_answer_url(course_id, class_id, cpi, _exam_id)
            parsed = self.get_question_report(_answer_url)
            diagnostics.extend(parsed.diagnostics)
            for question in parsed.questions:
                questions.append(Question(
                    len(questions) + 1,
                    question.stem,
                    question.answer,
                    question.status,
                    question.options,
                ))
            logger.info('共 {} 个题目，其中 {} 个待人工检查', len(questions), sum(not item.answer for item in questions))

        if not _dir_ids:
            diagnostics.append('课程未返回任何自测目录；该课程可能未开通自测或页面结构已变更')
        report = CrawlReport(str(course_id), course_name, questions, diagnostics)
        if report.incomplete_questions:
            report.diagnostics.append(f'有 {report.incomplete_questions} 题缺少答案节点，请检查页面结构或题型支持情况')
        self._write_exports(report, output_dir, formats)
        return report

def build_argument_parser():
    parser = argparse.ArgumentParser(
        description='导出学习通自测题库；仅支持当前账号可访问且已开通自测的课程。'
    )
    parser.add_argument('--course-id', help='要导出的自测课程 ID；省略时登录后交互输入')
    parser.add_argument('--class-id', help='页面无法自动解析时使用的 classId，必须与 --cpi 同时提供')
    parser.add_argument('--cpi', help='页面无法自动解析时使用的 cpi，必须与 --class-id 同时提供')
    parser.add_argument('--format', dest='formats', nargs='+', choices=('json', 'txt', 'xlsx'),
                        default=('json', 'txt'), help='导出格式，默认 json txt')
    parser.add_argument('--output-dir', default='out', help='导出目录，默认 out')
    parser.add_argument('--list-courses', action='store_true', help='登录后仅列出可访问的自测课程')
    parser.add_argument('--username', help='登录手机号；省略时交互输入')
    return parser


def _print_courses(client):
    print('以下仅为当前账号可访问、可用于本工具的“自测”课程；普通课程不在此列表不代表登录失败。')
    found = 0
    for school_id, school_name in client.get_schools():
        courses = client.get_courses(school_id)
        if not courses:
            continue
        print(f'{GREEN}{school_name} (school_id: {BLUE}{school_id}{GREEN}){RESET}')
        for course_id, course_name in courses:
            found += 1
            print(f'    {GREEN}{course_name} (course_id: {BLUE}{course_id}{GREEN}){RESET}')
    if not found:
        print('未找到可访问的自测课程。请确认课程已开通自测，或稍后重试。')


def main(argv=None):
    args = build_argument_parser().parse_args(argv)
    if bool(args.class_id) != bool(args.cpi):
        build_argument_parser().error('--class-id 和 --cpi 必须同时提供')

    client = XXT()
    username = args.username or input('输入手机号: ')
    password = getpass.getpass('输入密码: ')
    try:
        client.login(username, password)
        if args.list_courses or not (args.class_id and args.cpi):
            _print_courses(client)
        if args.list_courses:
            return 0

        course_id = args.course_id or input('请输入课程id(course_id): ').strip()
        if not course_id:
            raise CourseUnavailableError('未输入课程 ID。可先使用 --list-courses 查看可导出的自测课程。')
        report = client.crawl_course(
            course_id,
            class_id=args.class_id,
            cpi=args.cpi,
            output_dir=args.output_dir,
            formats=args.formats,
        )
    except XXTError as error:
        print(f'{RED}操作失败：{error}{RESET}')
        return 1
    except requests.RequestException as error:
        print(f'{RED}网络请求失败：{error}{RESET}')
        return 1

    print(f'导出完成：共 {report.total_questions} 题，完整解析 {report.complete_questions} 题，'
          f'待人工检查 {report.incomplete_questions} 题。')
    for diagnostic in report.diagnostics:
        print(f'{RED}提示：{diagnostic}{RESET}')
    for path in report.output_files:
        print(f'输出文件：{path.resolve()}')
    return 2 if report.incomplete_questions else 0


if __name__ == '__main__':
    raise SystemExit(main())

    
