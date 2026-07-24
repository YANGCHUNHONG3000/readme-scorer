# README Quality Scorer

评分：58/100  
AI 助手投入：~$5（DeepSeek API）  
代码行数：202  
依赖：requests

---

输入一个 GitHub 仓库地址或 `owner/repo`，输出它的 README 质量评分（0-100）和改进建议。

```bash
pip install requests
python readme_scorer.py owner/repo
```

## 做什么的

扫开源项目的 README，检查有没有常见问题：

- 缺安装指引
- 缺贡献说明
- 缺许可证
- 有占位符文本（TODO / Coming soon）
- 无 topics 标签
- 无 CI 配

## 为什么做

我在 GitHub 上找了几个开源项目帮修过 README（比如 `bm1549/home-assistant-frigidaire`、`versatiles-org/node-versatiles-container`），每修一个都要手动读一遍。索性写个脚本，10 秒出一个评分。

工具本身是用 DeepSeek V4 Flash 写的（~$5 的 API 调用），代码 200 行。够用就行。

## 用法

```bash
# 基础评分
python readme_scorer.py owner/repo

# 带死链检查（慢一些，有 API 限流）
python readme_scorer.py owner/repo --check-links
```

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
