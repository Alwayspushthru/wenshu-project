"""下载杭电指定场景的官方原件，提取可入库正文并记录来源（macOS）。"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "school_materials/hdu"
PREPARED = ROOT / "department_files/杭州电子科技大学"
FETCHED = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
PAGES = [
    ("教务处", "补办学位证明书、毕业证明书须知", "https://jwc.hdu.edu.cn/2025/0919/c13474a285891/page.htm", "2025-09-19"),
    ("图书馆", "图书馆校外访问指南", "https://tsg.hdu.edu.cn/xwfw/list.htm", None),
    ("电子信息学院", "研究生知识产权用印申请表", "https://ee.hdu.edu.cn/2021/0408/c13558a150894/page.htm", "2022-01-07"),
    ("电子信息学院", "关于启用研究生自助打印服务系统的通知", "https://ee.hdu.edu.cn/2021/0104/c13558a150895/page.htm", "2022-01-07"),
    ("电子信息学院", "研究生导师变更（转、增）申请表", "https://ee.hdu.edu.cn/2021/0928/c13558a150890/page.htm", "2022-01-07"),
    ("电子信息学院", "研究生增、退修课程申请表", "https://ee.hdu.edu.cn/2021/0928/c13558a150889/page.htm", "2022-01-07"),
]


def normalize_text(text):
    """清理转写正文的行尾空白，原始网页和附件保持不变。"""
    return "\n".join(line.rstrip() for line in text.splitlines()).strip() + "\n"


class ArticleParser(HTMLParser):
    """只读取官网正文容器，不将导航、脚本、页脚混入知识库。"""

    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
    BLOCK = {"p", "div", "section", "li", "tr", "h1", "h2", "h3", "h4"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.active_depth = None
        self.hidden = 0
        self.parts = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.active_depth is None and "wp_articlecontent" in attrs.get("class", "").split():
            self.active_depth = self.depth
        if self.active_depth is not None:
            if tag in {"script", "style"}:
                self.hidden += 1
            if tag in self.BLOCK or tag == "br":
                self.parts.append("\n")
            if tag == "a" and attrs.get("href"):
                self.links.append(attrs["href"])
            if tag in {"td", "th"}:
                self.parts.append(" | ")
        if tag not in self.VOID:
            self.depth += 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        self.depth -= 1
        if self.active_depth is not None:
            if tag in self.BLOCK:
                self.parts.append("\n")
            if tag in {"script", "style"} and self.hidden:
                self.hidden -= 1
            if self.depth == self.active_depth:
                self.active_depth = None

    def handle_data(self, data):
        if self.active_depth is not None and not self.hidden:
            self.parts.append(data)

    def text(self):
        lines = [re.sub(r"[\t \xa0]+", " ", s).strip() for s in "".join(self.parts).splitlines()]
        return "\n\n".join(s for s in lines if s)


def download(url, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        subprocess.run(["curl", "-L", "--fail", "--silent", "--show-error", "--max-time", "45", url, "-o", str(destination)], check=True)
    if not destination.stat().st_size:
        raise ValueError(f"下载文件为空: {destination}")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = []
    for dept, title, page_url, published in PAGES:
        original_title = "校外访问" if dept == "图书馆" else title
        original = ARCHIVE / "originals" / dept / f"{original_title}.html"
        download(page_url, original)
        parser = ArticleParser()
        parser.feed(original.read_text(encoding="utf-8"))
        body = parser.text()
        if len(body) < 8:
            raise ValueError(f"未提取到官网正文，拒绝生成空知识文档: {page_url}")
        attachments = []
        for href in dict.fromkeys(parser.links):
            if not href.lower().endswith(".doc"):
                continue
            url = urljoin(page_url, href)
            path = ARCHIVE / "originals" / dept / f"{title}.doc"
            download(url, path)
            if not path.read_bytes().startswith(bytes.fromhex("d0cf11e0a1b11ae1")):
                raise ValueError(f"下载内容不是原始Word文档: {url}")
            converted = subprocess.run(["textutil", "-convert", "txt", "-encoding", "UTF-8", "-stdout", str(path)], capture_output=True, check=True).stdout.decode("utf-8")
            if "杭州电子科技大学" not in converted:
                raise ValueError(f"附件转写缺少学校标识: {path}")
            body += f"\n\n## 官方附件正文\n\n附件下载地址：{url}\n\n以下为原始Word附件的纯文本转写，填写及提交请使用原件。\n\n{converted.strip()}\n"
            attachments.append({"source_url": url, "original_file": str(path.relative_to(ROOT)), "sha256": digest(path)})
        header = f"# 杭州电子科技大学{title}\n\n来源发布页：{page_url}\n\n来源部门：杭州电子科技大学{dept}\n\n采集日期：{FETCHED}\n\n"
        if published:
            header += f"官网页面显示的发布日期：{published}。以页面显示日期为准，不使用URL路径推断发布日期。\n\n"
        else:
            header += "官网正文未显示明确发布日期。\n\n"
        if published == "2022-01-07":
            header += "版本说明：这是官网公开的历史材料。自助打印通知落款为2020年11月19日。涉及现时办理地点、收费、联系人或流程时应向相关部门核实，不能推定截至采集日仍然不变。\n\n" if "自助打印" in title else "版本说明：这是官网公开的历史材料，当前办理流程和表格版本应向相关部门核实。\n\n"
        prepared = PREPARED / dept / f"{title}.md"
        prepared.parent.mkdir(parents=True, exist_ok=True)
        prepared.write_text(normalize_text(header + "## 官网正文\n\n" + body), encoding="utf-8")
        manifest.append({"title": title, "department": dept, "source_page": page_url, "page_published_at": published, "retrieved_at": FETCHED, "original_file": str(original.relative_to(ROOT)), "sha256": digest(original), "prepared_file": str(prepared.relative_to(ROOT)), "prepared_sha256": digest(prepared), "attachments": attachments})
    image = ARCHIVE / "originals/校历/杭州电子科技大学2025-2026学年校历.jpg"
    calendar_path = ROOT / "backend/app/school_profiles/hdu_calendar_2025_2026.json"
    calendar = json.loads(calendar_path.read_text(encoding="utf-8"))
    text = "# 杭州电子科技大学2025-2026学年校历\n\n来源：用户提供的校历图片；原图保存在school_materials/hdu/originals/校历/杭州电子科技大学2025-2026学年校历.jpg。\n\n适用学年：2025-2026。本材料不代表查询时的当前学期，其他学年不能套用。图片没有选课、退课或开题的截止日期。\n\n"
    for term in calendar["semesters"]:
        text += f"## {term['name']}\n\n"
        for key, label in [("staff_return_date", "教职工正式上班"), ("student_registration_date", "全体学生报到"), ("classes_start", "全体学生开始上课")]:
            if key in term:
                text += f"{label}：{term[key]}。\n\n"
        if "new_students" in term:
            v = term["new_students"]
            text += f"{v['applicable_to']}报到：{v['registration_date']}；始业教育（含开学典礼）：{v['orientation']['start']}至{v['orientation']['end']}。\n\n"
        periods = [("other_students_registration", "其他年级学生报到"), ("new_undergraduate_military_training", "本科新生军训"), ("sports_meeting", "校运动会"), ("graduation_education_and_departure", "本科生、研究生毕业教育及离校（含毕业典礼及学位授予仪式）"), ("exam_period", "全校停课考试")]
        for key, label in periods:
            if key in term:
                v = term[key]
                text += f"{label}：{v['start']}至{v['end']}。\n\n"
        for v in term["holidays"]:
            text += f"{v['name']}：" + (v["date"] if "date" in v else f"{v['start']}至{v['end']}") + "。\n\n"
        for v in term.get("makeup_classes", []):
            text += f"调课：{v['attendance_date']}补{v['replaces_date']}的课。\n\n"
        for key, label in [("student_winter_vacation_start", "全体学生开始放寒假"), ("student_summer_vacation_start", "全体学生开始放暑假"), ("staff_rotation_leave_start", "教职工开始轮休")]:
            if key in term:
                text += f"{label}：{term[key]}。\n\n"
        text += "\n\n".join(term["notes"]) + "\n\n"
    prepared = PREPARED / "教务处/校历/2025-2026学年校历.md"
    prepared.parent.mkdir(parents=True, exist_ok=True)
    prepared.write_text(normalize_text(text), encoding="utf-8")
    manifest.append({"title": "2025-2026学年校历", "department": "教务处", "source_type": "user_provided_image", "original_file": str(image.relative_to(ROOT)), "sha256": digest(image), "structured_file": str(calendar_path.relative_to(ROOT)), "prepared_file": str(prepared.relative_to(ROOT)), "prepared_sha256": digest(prepared)})
    (ARCHIVE / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已整理 {len(manifest)} 份可入库文本、{sum(len(x.get('attachments', [])) for x in manifest)} 份官方Word附件及来源校验记录。")


if __name__ == "__main__":
    main()
