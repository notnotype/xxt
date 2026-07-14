import unittest

from main import CourseUnavailableError, XXT


class FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        return None


class CourseParameterTests(unittest.TestCase):
    def test_uses_exam_answer_id_returned_by_the_start_page(self):
        client = XXT()
        client.get = lambda _: FakeResponse('redirect?examId=exam-1&examAnswerId=answer-9&')

        exam_id = client.get_exam_id("course", "class", "cpi", "directory")

        self.assertEqual("exam-1", exam_id)
        self.assertIn("examAnswerId=answer-9", client.get_answer_url("course", "class", "cpi", exam_id))

    def test_uses_manual_class_id_and_cpi_without_requesting_course_page(self):
        client = XXT()
        client.get = lambda _: self.fail("manual parameters should not request the course page")

        parameters = client.resolve_course_parameters("course-1", "class-1", "cpi-1")

        self.assertEqual(("class-1", "cpi-1"), parameters)

    def test_explains_when_course_has_no_self_test_parameters(self):
        client = XXT()
        client.get = lambda _: FakeResponse("<html><body>当前课程不允许自测</body></html>")

        with self.assertRaisesRegex(CourseUnavailableError, "未提供自测参数"):
            client.resolve_course_parameters("course-1")


if __name__ == "__main__":
    unittest.main()
