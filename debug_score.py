"""Debug README scoring"""
import requests, base64, re

proxy = {"https": "http://127.0.0.1:10809", "http": "http://127.0.0.1:10809"}
r = requests.get("https://api.github.com/repos/YANGCHUNHONG3000/readme-scorer/readme", proxies=proxy, timeout=10)
d = r.json()
content = base64.b64decode(d["content"]).decode("utf-8")
lower = content.lower()

# Search for placeholders
for p in ["todo", "coming soon", "lorem ipsum", "tbd", "wip"]:
    idx = lower.find(p)
    if idx >= 0:
        context = content[max(0,idx-40):idx+40]
        print(f'FOUND "{p}" at pos {idx}: ...{repr(context)}...')
    else:
        print(f'"{p}" not found')

print()
# Check install-related heading detection
headings = re.findall(r"^#{1,3}\s+(.+)$", content, re.MULTILINE)
print("Headings:", headings)

# Check the install/quick start regex
install_pattern = r"#+\s*(install|installation|quick ?start|getting started|setup)"
install_match = re.search(install_pattern, lower)
print(f"\nInstall regex match: {install_match.group() if install_match else 'NONE'}")
