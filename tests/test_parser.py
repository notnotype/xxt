import unittest

from main import QuestionParser, XXT


class QuestionParserTests(unittest.TestCase):
    def test_keeps_question_when_answer_node_is_missing(self):
        page = '''
        <div class="zm_box bgColor">第一题</div>
        <div class="zr_bg">正确答案：A</div>
        <div class="zm_box bgColor">第二题（填空）</div>
        '''

        report = QuestionParser().parse(page)

        self.assertEqual(2, report.source_question_count)
        self.assertEqual(0, report.parsed_question_count)
        self.assertEqual("第一题", report.questions[0].stem)
        self.assertEqual("正确答案：A", report.questions[0].answer)
        self.assertEqual("ambiguous_answer_mapping", report.questions[0].status)
        self.assertEqual("ambiguous_answer_mapping", report.questions[1].status)
        self.assertIn("答案对应关系不可靠", report.diagnostics[0])

    def test_legacy_question_answer_method_does_not_drop_missing_answer(self):
        class Response:
            text = '<div class="zm_box bgColor">第一题</div><div class="zr_bg">A</div><div class="zm_box bgColor">第二题</div>'

            def raise_for_status(self):
                return None

        client = XXT()
        client.get = lambda _: Response()

        self.assertEqual([("第一题", "A"), ("第二题", "")], client.get_question_answers("unused"))

    def test_extracts_multiple_choice_options_into_separate_fields(self):
        page = '<div class="zm_box bgColor">题干 A. 选项甲 B. 选项乙</div><div class="zr_bg">正确答案：B</div>'

        question = QuestionParser().parse(page).questions[0]

        self.assertEqual("题干", question.stem)
        self.assertEqual({"A": "选项甲", "B": "选项乙"}, question.options)

    def test_marks_empty_answer_element_as_missing_answer(self):
        page = '<div class="zm_box bgColor">填空题</div><div class="zr_bg"></div>'

        question = QuestionParser().parse(page).questions[0]

        self.assertEqual("missing_answer", question.status)


if __name__ == "__main__":
    unittest.main()
