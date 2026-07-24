#!/usr/bin/env python3
"""
README Quality Scorer
输入一个 GitHub 仓库 URL 或 owner/repo,输出 0-100 分的 README 质量报告。

用法:
    python readme_scorer.py owner/repo
    python readme_scorer.py https://github.com/owner/repo
    python readme_scorer.py owner/repo --check-links   # 额外检查死链,较慢

依赖:
    pip install requests

可选:
    设置环境变量 GITHUB_TOKEN 可以把 API 限额从 60次/小时 提升到 5000次/小时
    export GITHUB_TOKEN=***
"""

import os
import re
import sys
import base64
import argparse
from urllib.parse import urlparse

import requests

GITHUB_API = "https://api.github.com"


def parse_repo(input_str):
    """从 URL 或 owner/repo 字符串里解析出 owner 和 repo"""
    input_str = input_str.strip()
    if input_str.startswith("http"):
        path = urlparse(input_str).path.strip("/")
        parts = path.split("/")
        if len(parts) < 2:
            raise ValueError(f"无法解析仓库地址: {input_str}")
        return parts[0], parts[1]
    parts = input_str.split("/")
    if len(parts) != 2:
        raise ValueError(f"无法解析仓库地址: {input_str}")
    return parts[0], parts[1]


def get_headers():
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_repo_meta(owner, repo, headers):
    url = f"{GITHUB_API}/repos/{owner}/{repo}"
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()


def fetch_readme(owner, repo, headers):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/readme"
    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    data = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
    return content


def fetch_contents_list(owner, repo, headers, path=""):
    """列出某个目录下的文件名,失败(比如目录不存在)返回空列表"""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code != 200:
        return []
    data = r.json()
    if isinstance(data, list):
        return [item["name"] for item in data]
    return []


def check_dead_links(text, max_links=15, timeout=5):
    """粗略检查 README 里的外链是否可访问,最多检查 max_links 个避免太慢/被限流"""
    urls = re.findall(r'\]\((https?://[^\s\)]+)', text)
    urls = list(dict.fromkeys(urls))[:max_links]  # 去重 + 限量
    dead = []
    for u in urls:
        try:
            resp = requests.head(u, timeout=timeout, allow_redirects=True)
            if resp.status_code >= 400:
                resp = requests.get(u, timeout=timeout, allow_redirects=True)
                if resp.status_code >= 400:
                    dead.append((u, resp.status_code))
        except requests.RequestException:
            dead.append((u, "unreachable"))
    return dead


def score_readme(owner, repo, meta, readme_text, root_files, headers):
    checks = []  # (描述, 分值变化, 是否正向)
    score = 0

    if readme_text is None:
        return 0, [("仓库没有 README 文件", -100, False)]

    lower = readme_text.lower()
    lines = [l for l in readme_text.splitlines() if l.strip()]

    # +10 项目名 + 一句话描述
    has_title = bool(re.search(r'^#\s+\S', readme_text, re.MULTILINE))
    has_desc = bool(meta.get("description")) or len(lines) > 1
    if has_title and has_desc:
        score += 10
        checks.append(("有项目名称和一句话描述", 10, True))
    else:
        checks.append(("缺少清晰的项目名称/描述", 0, False))

    # +10 安装/快速开始
    if re.search(r'#+\s*(install|installation|quick ?start|getting started|setup)', lower) or \
       "pip install" in lower or "pip3 install" in lower:
        score += 10
        checks.append(("有安装/快速开始步骤", 10, True))
    else:
        checks.append(("缺少安装/快速开始章节", 0, False))

    # +10 使用示例
    if re.search(r'#+\s*(usage|example|examples)', lower) or "```" in readme_text:
        score += 10
        checks.append(("有使用示例", 10, True))
    else:
        checks.append(("缺少使用示例", 0, False))

    # +10 license
    has_license_badge = "license" in lower
    has_license_file = meta.get("license") is not None
    if has_license_badge or has_license_file:
        score += 10
        checks.append(("有许可证信息或 badge", 10, True))
    else:
        checks.append(("缺少许可证信息", 0, False))

    # +10 contribution 指引
    has_contrib_section = bool(re.search(r'#+\s*contribut', lower))
    has_contrib_file = any(f.lower().startswith("contributing") for f in root_files)
    if has_contrib_section or has_contrib_file:
        score += 10
        checks.append(("有 Contribution 指引", 10, True))
    else:
        score -= 10
        checks.append(("无 Contribution 指引", -10, False))

    # +10 API/配置文档链接
    if re.search(r'#+\s*(api|configuration|config|docs|documentation)', lower) or \
       re.search(r'\]\(https?://[^\)]*docs[^\)]*\)', lower):
        score += 10
        checks.append(("有 API/配置文档链接", 10, True))
    else:
        checks.append(("无 API/配置文档链接", 0, False))

    # -15 太短
    if len(lines) < 50:
        score -= 15
        checks.append((f"README 过短 (仅 {len(lines)} 行非空内容)", -15, False))

    # -20 占位符
    # 排除表格行、代码块和已知关键词描述（如评分表里的说明文字）
    # 只检测 markdown 正文中的占位符
    lines_to_check = []
    for line in readme_text.splitlines():
        stripped = line.strip()
        # 跳过表格行 | 和代码块 ```
        if stripped.startswith("|") and stripped.endswith("|"):
            continue
        if stripped.startswith("```"):
            continue
        lines_to_check.append(stripped)
    plain_text = "\n".join(lines_to_check).lower()
    placeholders = ["todo", "coming soon", "lorem ipsum", "tbd", "wip"]
    found_ph = [p for p in placeholders if p in plain_text]
    if found_ph:
        score -= 20
        checks.append((f"包含占位符文本: {', '.join(found_ph)}", -20, False))

    # -10 无 topics
    topics = meta.get("topics", [])
    if not topics:
        score -= 10
        checks.append(("无 GitHub topics 标签", -10, False))
    else:
        checks.append((f"有 {len(topics)} 个 topics 标签", 0, True))

    # -10 无 CI badge / workflow
    has_ci_badge = bool(re.search(r'(github\.com/.*actions|shields\.io.*(build|ci|workflow))', lower))
    workflows = fetch_contents_list(owner, repo, headers, ".github/workflows")
    if not has_ci_badge and not workflows:
        score -= 10
        checks.append(("无 CI badge / workflow 配置", -10, False))
    else:
        checks.append(("检测到 CI 配置或 badge", 0, True))

    return max(0, min(100, score)), checks


def format_report(owner, repo, score, checks, dead_links=None):
    good = [c for c, s, ok in checks if ok]
    bad = [c for c, s, ok in checks if not ok]

    emoji = "🟢" if score >= 80 else "🟡" if score >= 50 else "🔴"

    report = f"# README Quality Report for {owner}/{repo}\n\n"
    report += f"## Score: {score}/100 {emoji}\n\n"
    if good:
        report += "### ✅ 做得好\n"
        for g in good:
            report += f"- {g}\n"
        report += "\n"
    if bad:
        report += "### ❌ 需要改进\n"
        for b in bad:
            report += f"- {b}\n"
        report += "\n"
    if dead_links:
        report += "### 🔗 疑似死链\n"
        for url, status in dead_links:
            report += f"- {url} ({status})\n"
        report += "\n"

    report += "### 建议\n"
    tips = []
    if any("Contribution" in b for b in bad):
        tips.append("加 CONTRIBUTING.md 或对应章节")
    if any("CI" in b for b in bad):
        tips.append("加 GitHub Actions workflow 和对应 badge")
    if any("占位符" in b for b in bad):
        tips.append("移除 TODO / Coming soon 等占位符文本")
    if any("topics" in b for b in bad):
        tips.append("在仓库设置里补上 GitHub topics 标签")
    if any("过短" in b for b in bad):
        tips.append("补充更详细的说明、安装步骤和使用示例")
    for i, t in enumerate(tips, 1):
        report += f"{i}. {t}\n"

    return report


def main():
    parser = argparse.ArgumentParser(description="README Quality Scorer")
    parser.add_argument("repo", help="仓库地址,如 owner/repo 或完整 GitHub URL")
    parser.add_argument("--check-links", action="store_true", help="额外检查 README 中的死链(较慢,受限流影响)")
    args = parser.parse_args()

    try:
        owner, repo = parse_repo(args.repo)
    except ValueError as e:
        print(f"错误: {e}")
        sys.exit(1)

    headers = get_headers()

    try:
        meta = fetch_repo_meta(owner, repo, headers)
    except requests.RequestException as e:
        print(f"错误: 无法获取仓库信息 ({e})")
        print("提示: 未认证请求限额为 60次/小时,可设置 GITHUB_TOKEN 环境变量提升到 5000次/小时")
        sys.exit(1)

    readme_text = fetch_readme(owner, repo, headers)
    root_files = fetch_contents_list(owner, repo, headers)

    score, checks = score_readme(owner, repo, meta, readme_text, root_files, headers)

    dead_links = None
    if args.check_links and readme_text:
        dead_links = check_dead_links(readme_text)
        if dead_links:
            score = max(0, score - 15)

    report = format_report(owner, repo, score, checks, dead_links)
    print(report)


if __name__ == "__main__":
    main()
