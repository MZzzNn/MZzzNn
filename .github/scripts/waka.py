"""Fetch public WakaTime stats and write them into README.md between the waka markers."""
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request

RANGE = os.environ.get("TIME_RANGE", "last_7_days")
LANG_COUNT = int(os.environ.get("LANG_COUNT", "10"))
README = os.environ.get("README_PATH", "README.md")
BLOCKS = "⣀⣄⣤⣦⣶⣷⣿"
BAR_LEN = 25

USERNAME = os.environ.get("WAKATIME_USERNAME", "MZzzNn")

# WakaTime no longer accepts API keys outside editor plugins, so read the
# public stats instead (needs "Display languages publicly" in WakaTime settings).
req = urllib.request.Request(
    f"https://wakatime.com/api/v1/users/{USERNAME}/stats/{RANGE}",
    headers={
        "User-Agent": "MZzzNn-profile-readme/1.0 (GitHub Actions)",
        "Accept": "application/json",
    },
)
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)["data"]
except urllib.error.HTTPError as e:
    sys.exit(f"WakaTime API error {e.code} {e.reason}: {e.read().decode(errors='replace')[:500]}")

if not data.get("languages"):
    sys.exit(
        "WakaTime returned no languages. Turn on 'Display languages publicly' at "
        "https://wakatime.com/settings/profile (status: " + str(data.get("status")) + ")"
    )


def bar(percent: float) -> str:
    filled = percent / 100 * BAR_LEN
    full = int(filled)
    out = BLOCKS[-1] * full
    if full < BAR_LEN:
        out += BLOCKS[int((filled - full) * (len(BLOCKS) - 1))]
        out += BLOCKS[0] * (BAR_LEN - full - 1)
    return out


start = data["start"][:10]
end = data["end"][:10]
lines = [
    f"From: {start} - To: {end}",
    "",
    f"Total Time: {data.get('human_readable_total_including_other_language') or data.get('human_readable_total') or 'hidden'}",
    "",
]
for lang in data.get("languages", [])[:LANG_COUNT]:
    lines.append(f"{lang['name']:<30}{lang['text']:<16}{bar(lang['percent'])}   {lang['percent']:05.2f} %")

block = "<!--START_SECTION:waka-->\n\n```txt\n" + "\n".join(lines) + "\n```\n\n<!--END_SECTION:waka-->"

with open(README, encoding="utf-8") as f:
    readme = f.read()

pattern = re.compile(r"<!--START_SECTION:waka-->.*?<!--END_SECTION:waka-->", re.S)
if not pattern.search(readme):
    sys.exit("Could not find <!--START_SECTION:waka--> ... <!--END_SECTION:waka--> in README")

new = pattern.sub(lambda _: block, readme, count=1)
if new == readme:
    print("No changes")
else:
    with open(README, "w", encoding="utf-8") as f:
        f.write(new)
    print("README updated:\n" + block)
