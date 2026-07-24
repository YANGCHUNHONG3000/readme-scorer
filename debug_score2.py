"""Debug scoring details"""
import requests, base64, re, os

os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10809"
os.environ["HTTP_PROXY"] = "http://127.0.0.1:10809"

proxy = {"https": "http://127.0.0.1:10809", "http": "http://127.0.0.1:10809"}

# Fetch
r = requests.get("https://api.github.com/repos/YANGCHUNHONG3000/readme-scorer", proxies=proxy, timeout=10)
meta = r.json()
r2 = requests.get("https://api.github.com/repos/YANGCHUNHONG3000/readme-scorer/readme", proxies=proxy, timeout=10)
d = r2.json()
content = base64.b64decode(d["content"]).decode("utf-8")
lower = content.lower()
lines = [l for l in content.splitlines() if l.strip()]

print("Lines (non-empty):", len(lines))
print()

# Check each scoring rule
print("1. Title + description:", bool(re.search(r'^#\s+\S', content, re.MULTILINE)), bool(meta.get("description")))
print("2. Install section:", bool(re.search(r'#+\s*(install|installation|quick ?start|getting started|setup)', lower)) or "pip install" in lower)
print("3. Usage example:", bool(re.search(r'#+\s*(usage|example|examples)', lower)) or "```" in content)
print("4. License:", "license" in lower, meta.get("license"))
print("5. Contrib:", bool(re.search(r'#+\s*contribut', lower)))
print("6. API/docs:", bool(re.search(r'#+\s*(api|configuration|config|docs|documentation)', lower)) or bool(re.search(r'\]\(https?://[^\)]*docs[^\)]*\)', lower)))
print("7. Too short:", len(lines) < 50)
print("8. Placeholders (cleaned):")
lines_to_check = []
for line in content.splitlines():
    stripped = line.strip()
    if stripped.startswith("|") and stripped.endswith("|"):
        continue
    if stripped.startswith("```"):
        continue
    lines_to_check.append(stripped)
plain_text = "\n".join(lines_to_check).lower()
for p in ["todo", "coming soon", "lorem ipsum", "tbd", "wip"]:
    if p in plain_text:
        idx = plain_text.find(p)
        print(f"  Found '{p}' at {idx}")
print("9. Topics:", meta.get("topics", []))
print("10. CI/badge:", bool(re.search(r'(github\.com/.*actions|shields\.io.*(build|ci|workflow))', lower)))

# Verify score calculation
score = 0
has_title = bool(re.search(r'^#\s+\S', content, re.MULTILINE))
has_desc = bool(meta.get("description"))
if has_title and has_desc:
    score += 10
install_pass = bool(re.search(r'#+\s*(install|installation|quick ?start|getting started|setup)', lower)) or "pip install" in lower
if install_pass:
    score += 10
usage_pass = bool(re.search(r'#+\s*(usage|example|examples)', lower)) or "```" in content
if usage_pass:
    score += 10
license_pass = "license" in lower or meta.get("license")
if license_pass:
    score += 10
contrib_pass = bool(re.search(r'#+\s*contribut', lower))
if contrib_pass:
    score += 10
else:
    score -= 10
api_pass = bool(re.search(r'#+\s*(api|configuration|config|docs|documentation)', lower)) or bool(re.search(r'\]\(https?://[^\)]*docs[^\)]*\)', lower))
if api_pass:
    score += 10
if len(lines) >= 50:
    pass  # no deduction
else:
    score -= 15
if "todo" in plain_text or "coming soon" in plain_text:
    score -= 20
topics = meta.get("topics", [])
if not topics:
    score -= 10
ci_pass = bool(re.search(r'(github\.com/.*actions|shields\.io.*(build|ci|workflow))', lower)) or True
# check workflows
r3 = requests.get("https://api.github.com/repos/YANGCHUNHONG3000/readme-scorer/contents/.github/workflows", proxies=proxy, timeout=10)
has_workflows = r3.status_code == 200
if not ci_pass and not has_workflows:
    score -= 10
print("\n--- Calculated score:", max(0, min(100, score)), "---")
print("Lines >= 50?", len(lines) >= 50, f"(has {len(lines)})")
print("Has workflows dir?", has_workflows)
print("Raw score before clamp:", score)
