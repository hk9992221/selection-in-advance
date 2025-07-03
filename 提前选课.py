import os
import re
import requests
from urllib.parse import quote, unquote
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 自动从 Selenium 会话获取登录后 Cookie，并注入 requests.Session
LOGIN_URL = "https://authserver.cumt.edu.cn/authserver/login?service=http%3A%2F%2Fjwxt.cumt.edu.cn%2Fsso%2Fjziotlogin"  # 教务系统登录页面地址，可替换为具体的登录 URL
COURSE_FILE = "course_info.txt"

class BrowserLogin:
    @staticmethod
    def fetch_cookies():
        # 使用 Chrome 浏览器手动登录，登录完成后脚本继续
        options = Options()
        # 不启用 headless，这样方便手动输入验证码或二次验证
        # options.add_argument('--headless')
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()
        driver.get(LOGIN_URL)
        print("请在弹出的浏览器中完成登录，登录成功后在此终端按回车继续...")
        input()
        # 获取所有 cookie
        selenium_cookies = driver.get_cookies()
        driver.quit()
        # 转换为 requests 可用的 dict
        return {item['name']: item['value'] for item in selenium_cookies}

class CourseSelector:
    def __init__(self):
        # 通过 Selenium 登录并获取 Cookie
        cookies = BrowserLogin.fetch_cookies()
        self.session = requests.Session()
        self.session.cookies.update(cookies)

        # 加载可选课程
        self.courses = self._load_courses()

        # 动态参数占位
        self.dynamic_params = {
            "njdm_id": "",
            "zyh_id": "",
            "njdm_id_xs": "",
            "zyh_id_xs": "",
            "xkxnm": "2025",
            "xkxqm": "3",
            "xkkz_id": "",
            "jcxx_id": ""
        }
        self._extract_dynamic_params()

    def _extract_dynamic_params(self):
        url = f"http://jwxt.cumt.edu.cn/jwglxt/xsxk/zzxkyzb_cxZzxkYzbIndex.html?gnmkdm=N253512&layout=default"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": url
        }
        resp = self.session.get(url, headers=headers)
        html = resp.text
        # 使用正则从页面隐藏域提取参数
        for key in ["njdm_id", "zyh_id", "xkxnm", "xkxqm", "xkkz_id"]:
            m = re.search(rf'<input[^>]+id="{key}"[^>]+value="(.*?)"', html)
            if m:
                self.dynamic_params[key] = m.group(1)
        # 专业同学级兼容填写
        self.dynamic_params["njdm_id_xs"] = self.dynamic_params["njdm_id"]
        self.dynamic_params["zyh_id_xs"] = self.dynamic_params["zyh_id"]

    def _load_courses(self):
        if not os.path.exists(COURSE_FILE):
            print(f"错误：{COURSE_FILE} 不存在，请先获取课程列表。")
            return []
        courses = []
        with open(COURSE_FILE, 'r', encoding='utf-8') as f:
            cur = {}
            for line in f:
                line = line.strip()
                if not line and cur:
                    courses.append(cur)
                    cur = {}
                    continue
                if line.startswith("jxb_id:"):
                    cur['jxb_id'] = line.split(': ')[1]
                elif line.startswith("kch_id:"):
                    cur['kch_id'] = line.split(': ')[1]
                elif line.startswith("kch:"):
                    cur['kch'] = line.split(': ')[1]
                elif line.startswith("kcmc:"):
                    cur['kcmc'] = unquote(line.split(': ')[1])
        print(f"已加载 {len(courses)} 门课程。")
        return courses

    def _select_course(self, course):
        url = "http://jwxt.cumt.edu.cn/jwglxt/xsxk/zzxkyzbjk_xkBcZyZzxkYzb.html?gnmkdm=N253512"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"http://jwxt.cumt.edu.cn/jwglxt/xsxk/zzxkyzb_cxZzxkYzbIndex.html?gnmkdm=N253512&layout=default"
        }
        data = {
            "jxb_ids": course['jxb_id'],
            "kch_id": course['kch_id'],
            "kcmc": quote(course['kcmc']),
            "xklc": "1",
            **self.dynamic_params
        }
        resp = self.session.post(url, headers=headers, data=data)
        try:
            return resp.json().get('flag') == '1'
        except:
            return False

    def run(self):
        if not self.courses:
            return
        while True:
            for i, c in enumerate(self.courses[:5], 1):
                print(f"[{c['kch']}] {c['kcmc']}")
            choice = input("输入课程代码或 q 退出：").strip()
            if choice.lower() == 'q': break
            if choice.lower() == 'all':
                for c in self.courses:
                    print(f"[{c['kch']}] {c['kcmc']}")
                continue
            course = next((c for c in self.courses if c['kch']==choice), None)
            if not course:
                print("未找到，请重试。")
                continue
            print(f"选课 {course['kcmc']} ...")
            print("成功" if self._select_course(course) else "失败")
            if input("继续？(y/n)").lower() != 'y': break

if __name__ == '__main__':
    selector = CourseSelector()
    selector.run()
