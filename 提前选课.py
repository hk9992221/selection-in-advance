import requests
from urllib.parse import quote, unquote
import os
import re

# 全局配置
COOKIES = {
    "JSESSIONID": "*************",
    "route": "**********"
}#需要改成自己的，通过网络请求查看cookie: //打开浏览器的开发者工具,切换到"Network"标签,刷新页面,即可看到每个网络请求所携带的cookie信息。 

xkkz_id="38D3AE0AC713C20FE0631E70A8C0B842"  # 需要改成高年级的，已配置2022级的

BASE_URL = "http://jwxt.cumt.edu.cn"
COURSE_FILE = "course_info.txt"

class CourseSelector:
    def __init__(self):
        self.session = requests.Session()
        self.session.cookies.update(COOKIES)
        self.courses = self._load_courses()
        # 新增提取的参数
        self.dynamic_params = {
            "njdm_id": "",
            "zyh_id": "",
            "njdm_id_xs": "",
            "zyh_id_xs": "",
            "xkxnm": "2025",
            "xkxqm": "3",
            "jcxx_id": ""
        }
        self._extract_dynamic_params()

    def _extract_dynamic_params(self):
        """从页面提取动态参数"""
        url = f"{BASE_URL}/jwglxt/xsxk/zzxkyzb_cxZzxkYzbIndex.html?gnmkdm=N253512&layout=default"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Cookie": f"JSESSIONID={COOKIES['JSESSIONID']}; route={COOKIES['route']}"
        }
        
        try:
            response = self.session.get(url, headers=headers)
            html = response.text
            # 提取参数
            self.dynamic_params["njdm_id"] = re.search(r'<input.*?id="njdm_id".*?value="(.*?)"/>', html).group(1)
            self.dynamic_params["zyh_id"] = re.search(r'<input.*?id="zyh_id".*?value="(.*?)"/>', html).group(1)
            self.dynamic_params["njdm_id_xs"] = self.dynamic_params["njdm_id"]
            self.dynamic_params["zyh_id_xs"] = self.dynamic_params["zyh_id"]
            # 新增提取xkxnm和xkxqm
            self.dynamic_params["xkxnm"] = re.search(r'<input.*?id="xkxnm".*?value="(.*?)"/>', html).group(1)
            self.dynamic_params["xkxqm"] = re.search(r'<input.*?id="xkxqm".*?value="(.*?)"/>', html).group(1)
            # jcxx_id通常留空即可
        except Exception as e:
            print(f"参数提取失败，使用默认值: {str(e)}")

    # 以下是原有代码保持不变
    def _load_courses(self):
        """从文件加载课程信息"""
        if not os.path.exists(COURSE_FILE):
            print(f"错误：课程文件 {COURSE_FILE} 不存在，请先运行获取课程信息的脚本")
            return []
        
        courses = []
        with open(COURSE_FILE, "r", encoding="utf-8") as f:
            current_course = {}
            for line in f:
                line = line.strip()
                if not line:
                    if current_course:
                        courses.append(current_course)
                        current_course = {}
                    continue
                
                if line.startswith("jxb_id:"):
                    current_course["jxb_id"] = line.split(": ")[1]
                elif line.startswith("kch_id:"):
                    current_course["kch_id"] = line.split(": ")[1]
                elif line.startswith("kch:"):
                    current_course["kch"] = line.split(": ")[1]
                elif line.startswith("kcmc:"):
                    current_course["kcmc"] = unquote(line.split(": ")[1])
        
        print(f"已加载 {len(courses)} 门课程")
        return courses

    def _select_course(self, course):
        """发送选课请求"""
        url = f"{BASE_URL}/jwglxt/xsxk/zzxkyzbjk_xkBcZyZzxkYzb.html?gnmkdm=N253512"
        
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Host": "jwxt.cumt.edu.cn",
            "Origin": BASE_URL,
            "Referer": f"{BASE_URL}/jwglxt/xsxk/zzxkyzb_cxZzxkYzbIndex.html?gnmkdm=N253512&layout=default",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        data = {
            "jxb_ids": course["jxb_id"],
            "kch_id": course["kch_id"],
            "kcmc": quote(course["kcmc"]),
            "rwlx": "2", "rlkz": "0", "cdrlkz": "0", "rlzlkz": "1", "sxbj": "1",
            "xxkbj": "0", "qz": "0", "cxbj": "0", "xkkz_id": xkkz_id,
            "kklxdm": "10", "xklc": "1",
            # 使用提取的动态参数
            **self.dynamic_params
        }
        
        try:
            response = self.session.post(url, headers=headers, data=data)
            response.raise_for_status()
            result = response.json()
            return result.get("flag") == "1"
        except Exception as e:
            print(f"选课请求失败: {str(e)}")
            return False

    def _search_course(self, kch):
        """通过kch搜索课程"""
        for course in self.courses:
            if course.get("kch") == kch:
                return course
        return None

    def run(self):
        """主运行逻辑"""
        if not self.courses:
            return
        
        while True:
            print("\n当前课程列表（前5门）：")
            for i, course in enumerate(self.courses[:5], 1):
                print(f"[{course['kch']}] {course['kcmc']}")
            
            if len(self.courses) > 5:
                print(f"...共 {len(self.courses)} 门课程（输入 'all' 查看全部）")
            
            user_input = input("\n请输入课程代码（如 Q2415325），或输入 q 退出：").strip()
            
            if user_input.lower() == 'q':
                break
            elif user_input.lower() == 'all':
                for i, course in enumerate(self.courses, 1):
                    print(f"{i}. [{course['kch']}] {course['kcmc']}")
                continue
            
            course = self._search_course(user_input)
            if not course:
                print(f"未找到课程代码 {user_input}，请检查输入")
                continue
            
            print(f"\n准备选择课程：{course['kcmc']}")
            if self._select_course(course):
                print("✅ 选课成功！")
            else:
                print("❌ 选课失败")
            
            if input("是否继续选课？(y/n) ").lower() != 'y':
                break

if __name__ == "__main__":
    print("=== 通识课提前选课系统 ===")
    selector = CourseSelector()
    selector.run()
    print("程序结束")