import unittest

from main import LoginError, SessionExpiredError, XXT


class Response:
    def __init__(self, payload=None, text=""):
        self.payload = payload
        self.text = text

    def raise_for_status(self):
        return None

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class SessionTests(unittest.TestCase):
    def test_login_reports_non_json_response_as_actionable_error(self):
        client = XXT()
        client.post = lambda *_args, **_kwargs: Response(ValueError("not json"), "<html>login</html>")

        with self.assertRaisesRegex(LoginError, "登录接口未返回有效数据"):
            client.login("user", "password")

    def test_school_list_reports_expired_session_instead_of_key_error(self):
        client = XXT()
        client.get = lambda _: Response({"message": "please login"})

        with self.assertRaisesRegex(SessionExpiredError, "登录状态已失效"):
            client.get_schools()


if __name__ == "__main__":
    unittest.main()
