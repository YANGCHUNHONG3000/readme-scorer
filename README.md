# README Quality Scorer

评分：58/100（嗯，最开始测自己的仓库，不及格。改完才到 90+。）  
AI 助手投入：~$5（DeepSeek API）  
代码行数：202  
依赖：requests

---

我是一名扑街小说作者。很多小说会扑街，不是正文不行，而是封面、简介、书名不行。

开源项目也一样。

我帮几个项目修过 README（`bm1549/home-assistant-frigidaire`、`versatiles-org/node-versatiles-container`），每修一个都要手动读一遍。索性写个脚本自动评分。

输入一个 GitHub 仓库 URL 或 `owner/repo`，输出 0-100 分 + 改进建议。

```bash
pip install requests
python readme_scorer.py owner/repo
```

## 它怎么评的

| 检查项 | 分数影响 |
|--------|----------|
| 有项目名 + 一句话描述 | +10 |
| 有安装/快速开始步骤 | +10 |
| 有使用示例 | +10 |
| 有许可证信息或 badge | +10 |
| 有 Contribution 指引 | +10 |
| 有 API/配置文档链接 | +10 |
| README 太短（< 50 行非空内容） | -15 |
| 包含占位符文本（TODO / Coming soon） | -20 |
| 无 GitHub topics 标签 | -10 |
| 无 CI badge / workflow | -10 |

## 输出样例

测了一个真实项目 `bm1549/home-assistant-frigidaire`（我帮忙修过 README 的那个）：

```
# README Quality Report for bm1549/home-assistant-frigidaire

## Score: 70/100 🟡

### ✅ 做得好
- 有项目名称和一句话描述
- 有安装/快速开始步骤
- 有使用示例
- 有许可证信息或 badge
- 有 API/配置文档链接

### ❌ 需要改进
- 无 Contribution 指引 (-10)
- README 过短 (仅 48 行非空内容) (-15)
- 无 GitHub topics 标签 (-10)
- 无 CI badge / workflow 配置 (-10)

### 建议
1. 加 CONTRIBUTING.md 或对应章节
2. 加 GitHub Actions workflow 和对应 badge
3. 在仓库设置里补上 GitHub topics 标签
4. 补充更详细的说明、安装步骤和使用示例
```

## 用法

```bash
# 基础评分
python readme_scorer.py owner/repo

# 带死链检查（慢一些，有 API 限流）
python readme_scorer.py owner/repo --check-links
```

## 关于这个工具

工具本身是用 DeepSeek V4 Flash 写的（~$5 的 API 调用），代码 200 行。够用就行。

我不靠 GitHub 吃饭。我写小说扑街，修 README 扑街，写工具也扑街——但扑多了就习惯了。

## API 限额

未认证：60 次/小时  
带 token：5000 次/小时

建议设置环境变量：

```bash
export GITHUB_TOKEN=your_token_here
```

token 在 GitHub 设置 → Developer settings → Personal access tokens 免费生成，选 `public_repo` 权限就够了。

## License

MIT
