"""Fetch public WakaTime stats and write them into README.md between the waka markers."""
import json
import os
import re
import sys
import time
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


def skip(msg: str) -> None:
    """Temporary WakaTime problem: keep README as is and don't fail the run."""
    print(f"::warning::{msg} - README left unchanged, will retry on next schedule")
    sys.exit(0)


data = None
for attempt in range(3):
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.load(resp)
        if resp.status == 202:  # stats still being calculated
            raise TimeoutError("stats are still being calculated (202)")
        data = body["data"]
        break
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:500]
        if e.code < 500 and e.code != 429:
            sys.exit(f"WakaTime API error {e.code} {e.reason}: {detail}")
        err = f"WakaTime API error {e.code} {e.reason}: {detail}"
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError) as e:
        err = f"WakaTime request failed: {e}"
    print(f"Attempt {attempt + 1} failed: {err}")
    time.sleep(30)
else:
    skip(err)

if not data.get("languages"):
    if data.get("is_up_to_date") is False:
        skip("WakaTime stats are still updating")
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
