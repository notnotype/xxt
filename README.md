# 学习通自测题库导出工具

从学习通**已开通自测且当前账号可访问**的课程中导出题目。它不会自动答题，也不能导出没有自测入口的普通课程。

## 安装

需要 Python 3.10 或更高版本：

```shell
git clone https://github.com/notnotype/xxt.git
cd xxt
python -m pip install -r requirements.txt
```

## 使用

先列出当前账号可导出的自测课程：

```shell
python main.py --list-courses
```

导出指定课程（默认生成 JSON 和 TXT）：

```shell
python main.py --course-id 课程ID
```

同时生成可筛选的 Excel 文件：

```shell
python main.py --course-id 课程ID --format json txt xlsx --output-dir out
```

当课程页面结构变化、自动获取不到参数时，可以在已知参数的前提下使用恢复路径；`classId` 与 `cpi` 必须同时提供：

```shell
python main.py --course-id 课程ID --class-id 班级ID --cpi CPI
```

程序会在结束时打印每个输出文件的绝对路径，并报告总题数、完整解析数和待人工检查数。若题目缺少答案节点会标记为 `missing_answer`；题目/答案节点数量不一致时会标记为 `ambiguous_answer_mapping`。这两种情况都会以状态码 `2` 退出，避免把不完整导出误判为成功。

## 课程范围与常见问题

- 课程不出现在列表中，不代表登录失败；该列表只显示本工具能访问的**自测课程**。
- “未提供自测参数”表示课程没有开通兼容的自测页面，或页面结构已经变化；可检查课程是否存在自测入口，或在已知参数时使用上面的恢复路径。
- 请不要在 issue、截图或聊天中公开账号、密码、Cookie 或令牌。
- 登录和学校列表请求使用 HTTPS；密码仅在当前终端通过隐藏输入读取。

## 输出格式

- JSON：题号、题干、选项、答案和解析状态，便于后续处理。
- TXT：便于直接阅读。
- XLSX：题干、A–F 选项、答案和解析状态分列，便于筛选。

## 开发与验证

```shell
python -m unittest discover -s tests -v
python -m py_compile main.py
```

测试使用脱敏 HTML 夹具/模拟响应，不需要真实账号。

## 声明

请仅用于个人学习，并遵守学校与平台的使用规则。
