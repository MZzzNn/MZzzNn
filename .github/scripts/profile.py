"""Generate the animated SVG cards used in the profile README.

Static cards (header, stack, footer) are rebuilt from the config below.
Live cards (coding activity, stats, featured projects) use WakaTime public
stats and the GitHub API. If a live source is temporarily unavailable the
existing card is kept, so a scheduled run never breaks the profile.
"""
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from xml.sax.saxutils import escape

USER = "MZzzNn"
NAME = "Mazen Mohamed"
TAGLINE = "Building clean, well-architected apps for mobile and web  ·  Egypt"
ROLES = ["Software Engineer", "Mobile & Web Developer", "Flutter Package Author", "Open-Source Contributor"]
ORBIT = ["Flutter", "React", "Laravel", "Firebase", "Node.js", "Python"]
STACK = [
    ("Mobile", ["Flutter", "Dart", "Android", "iOS", "BLE", "Maps", "ML in Flutter"]),
    ("Web", ["React", "TypeScript", "JavaScript", "Vite", "HTML", "CSS", "Bootstrap"]),
    ("Backend", ["PHP", "Laravel", "Node.js", "Python", "Java", "C#", "Socket.IO"]),
    ("Data", ["Firebase", "MySQL", "MongoDB", "SQLite", "REST APIs"]),
    ("Tooling", ["Git", "GitHub Actions", "CI/CD", "Postman", "IntelliJ IDEA", "Adobe XD"]),
]
FEATURED = [
    "FlutterRoadmap",
    "Flutter_CI-CD_Pipeline",
    "Problem-Solving-Challenge",
    "magic_dropdown_search",
    "flutter_machine",
    "audio_video_flutter",
]
# Must match "Display code time publicly" range on wakatime.com/settings/profile
WAKA_RANGE = os.environ.get("TIME_RANGE", "all_time")
LANG_COUNT = int(os.environ.get("LANG_COUNT", "8"))
OUT = os.environ.get("OUT_DIR", "assets/generated")

CYAN, VIOLET, TEXT, MUTED = "#54c5f8", "#7c5cff", "#e6edf7", "#9aa7bd"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
LANG_COLORS = {
    "Dart": "#00B4AB", "Python": "#3572A5", "YAML": "#cb171e", "JSON": "#f5a623", "Markdown": "#4f8cff",
    "XML": "#0aa5c2", "Bash": "#89e051", "Shell": "#89e051", "Kotlin": "#A97BFF", "Groovy": "#4298b8",
    "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "PHP": "#777BB4", "HTML": "#e34c26", "CSS": "#663399",
    "Java": "#b07219", "C++": "#f34b7d", "Swift": "#F05138", "C#": "#178600", "Other": "#6b7a90", "Text": "#8b98ad",
}
PALETTE = [CYAN, VIOLET, "#22d3a6", "#f5a623", "#ff6b9a", "#4f8cff"]


def color_for(name: str) -> str:
    return LANG_COLORS.get(name) or PALETTE[sum(map(ord, name)) % len(PALETTE)]


def num(v: float) -> str:
    return f"{v:.3f}".rstrip("0").rstrip(".")


def card(w: int, h: int, body: str, defs: str = "", label: str = "", blobs: bool = True) -> str:
    """Shared dark card: gradient background, drifting glow, dot grid, animated border."""
    glow = f"""
    <g filter="url(#blur)">
      <circle cx="{w - 220}" cy="40" r="120" fill="{CYAN}" opacity=".22">
        <animate attributeName="cx" dur="15s" repeatCount="indefinite" values="{w - 220};{w - 360};{w - 160};{w - 220}"/>
      </circle>
      <circle cx="120" cy="{h}" r="110" fill="{VIOLET}" opacity=".22">
        <animate attributeName="cx" dur="18s" repeatCount="indefinite" values="120;260;80;120"/>
      </circle>
    </g>""" if blobs else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="{escape(label)}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b1220"/><stop offset="1" stop-color="#111a2e"/></linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient>
    <linearGradient id="border" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{w}" y2="{h}">
      <stop offset="0" stop-color="{CYAN}" stop-opacity=".9"/><stop offset=".5" stop-color="#ffffff" stop-opacity=".06"/><stop offset="1" stop-color="{VIOLET}" stop-opacity=".9"/>
      <animateTransform attributeName="gradientTransform" type="rotate" from="0 {w / 2} {h / 2}" to="360 {w / 2} {h / 2}" dur="10s" repeatCount="indefinite"/>
    </linearGradient>
    <filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="60"/></filter>
    <pattern id="dots" width="28" height="28" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.2" fill="#ffffff" opacity=".06"/></pattern>
    <clipPath id="card"><rect width="{w}" height="{h}" rx="18"/></clipPath>
{defs}  </defs>
  <style>
    .t{{font:700 26px {SANS};fill:{TEXT}}}
    .k{{font:600 14px {SANS};fill:{MUTED};letter-spacing:2px}}
    .s{{font:400 18px {SANS};fill:{MUTED}}}
    .b{{font:600 18px {SANS};fill:{TEXT}}}
    .m{{font:500 17px {MONO};fill:{MUTED}}}
  </style>
  <g clip-path="url(#card)">
    <rect width="{w}" height="{h}" fill="url(#bg)"/>{glow}
    <rect width="{w}" height="{h}" fill="url(#dots)"/>
  </g>
  <rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="17" fill="none" stroke="url(#border)" stroke-width="2"/>
{body}</svg>
"""


def header_svg() -> str:
    w, h, x0, cw = 1200, 320, 84, 15.6
    n = len(ROLES)
    dur = 3 * n
    widths = [round(len(r) * cw, 1) for r in ROLES]
    defs, texts, cur_v, cur_k = "", "", [], []
    for i, (role, rw) in enumerate(zip(ROLES, widths)):
        s = i / n
        kt = [0, s, s + 0.37 / n, s + 0.8 / n, s + 0.93 / n, 1]
        defs += (
            f'    <clipPath id="c{i}"><rect x="{x0}" y="160" height="44" width="0">'
            f'<animate attributeName="width" dur="{dur}s" repeatCount="indefinite" values="0;0;{rw};{rw};0;0" '
            f'keyTimes="{";".join(num(k) for k in kt)}"/></rect></clipPath>\n'
        )
        texts += (
            f'  <text x="{x0}" y="192" class="role" textLength="{rw}" lengthAdjust="spacing" '
            f'clip-path="url(#c{i})">{escape(role)}</text>\n'
        )
        cur_v += [x0, x0 + rw, x0 + rw, x0]
        cur_k += kt[1:5]
    cur_v.append(x0)
    cur_k.append(1)

    def ring(labels, radius, secs, direction):
        cx, cy = 960, 160
        out = (
            f'  <circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="#ffffff" stroke-opacity=".12" '
            f'stroke-dasharray="3 9"/>\n  <g>\n'
            f'    <animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" '
            f'to="{360 * direction} {cx} {cy}" dur="{secs}s" repeatCount="indefinite"/>\n'
        )
        for j, label in enumerate(labels):
            ang = 2 * math.pi * j / len(labels)
            px, py = cx + radius * math.cos(ang), cy + radius * math.sin(ang)
            cwid = len(label) * 10.5 + 30
            out += (
                f'    <g class="chip"><animateTransform attributeName="transform" type="rotate" '
                f'from="0 {num(px)} {num(py)}" to="{-360 * direction} {num(px)} {num(py)}" dur="{secs}s" repeatCount="indefinite"/>'
                f'<rect x="{num(px - cwid / 2)}" y="{num(py - 19)}" width="{num(cwid)}" height="38" rx="19"/>'
                f'<text x="{num(px)}" y="{num(py + 6)}" text-anchor="middle">{escape(label)}</text></g>\n'
            )
        return out + "  </g>\n"

    body = f"""  <style>
    .name{{font:700 66px {SANS};fill:url(#nm);letter-spacing:-1px}}
    .role{{font:500 26px {MONO};fill:{CYAN}}}
    .chip rect{{fill:#101a30;stroke:#ffffff;stroke-opacity:.2}}
    .chip text{{font:600 16px {SANS};fill:#dbe7ff}}
  </style>
  <text x="{x0 - 4}" y="126" class="name">{escape(NAME)}</text>
{texts}  <rect y="166" width="3" height="32" rx="1.5" fill="{CYAN}">
    <animate attributeName="x" dur="{dur}s" repeatCount="indefinite" values="{";".join(num(v + 4) for v in cur_v)}" keyTimes="{";".join(num(k) for k in cur_k)}"/>
    <animate attributeName="opacity" dur="0.9s" repeatCount="indefinite" values="1;1;0;0" keyTimes="0;0.5;0.5;1"/>
  </rect>
  <text x="{x0}" y="248" class="s">{escape(TAGLINE)}</text>
{ring(ORBIT, 126, 44, 1)}  <circle cx="960" cy="160" r="62" fill="none" stroke="url(#accent)" stroke-opacity=".5" stroke-dasharray="2 10" stroke-linecap="round">
    <animateTransform attributeName="transform" type="rotate" from="360 960 160" to="0 960 160" dur="24s" repeatCount="indefinite"/>
  </circle>
  <circle cx="960" cy="160" r="26" fill="url(#accent)">
    <animate attributeName="r" dur="3s" repeatCount="indefinite" values="24;28;24"/>
  </circle>
  <text x="960" y="167" text-anchor="middle" style="font:700 18px {MONO};fill:#0b1220">&lt;/&gt;</text>
"""
    defs += f'    <linearGradient id="nm" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#9fd8ff"/></linearGradient>\n'
    return card(w, h, body, defs, f"{NAME} - " + ", ".join(ROLES))


def stack_svg() -> str:
    w, row_h, top = 1200, 62, 96
    h = top + row_h * len(STACK) + 18
    body = '  <text x="60" y="62" class="t">Tech I work with</text>\n'
    idx = 0
    for r, (group, items) in enumerate(STACK):
        y = top + r * row_h
        body += f'  <text x="60" y="{y + 26}" class="k">{escape(group.upper())}</text>\n'
        x = 220
        for item in items:
            cw = len(item) * 10.2 + 46
            delay = num(0.15 + idx * 0.07)
            pulse = num((idx * 0.37) % 4)
            col = PALETTE[idx % len(PALETTE)]
            body += (
                f'  <g opacity="0"><animate attributeName="opacity" begin="{delay}s" dur="0.5s" from="0" to="1" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" begin="{delay}s" dur="0.5s" from="0 12" to="0 0" fill="freeze"/>'
                f'<rect x="{num(x)}" y="{y}" width="{num(cw)}" height="40" rx="20" fill="#ffffff" fill-opacity=".05" stroke="#ffffff" stroke-opacity=".14"/>'
                f'<circle cx="{num(x + 20)}" cy="{y + 20}" r="5" fill="{col}"><animate attributeName="opacity" begin="{pulse}s" dur="4s" repeatCount="indefinite" values="1;.35;1"/></circle>'
                f'<text x="{num(x + 34)}" y="{y + 26}" class="b" style="font-size:17px">{escape(item)}</text></g>\n'
            )
            x += cw + 12
            idx += 1
    return card(w, h, body, label="Tech stack: " + "; ".join(f"{g}: {', '.join(i)}" for g, i in STACK))


def footer_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 90" width="100%" preserveAspectRatio="none" role="img" aria-label="">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient></defs>
  <path fill="url(#g)" opacity=".35" d="M0 50 Q150 10 300 50 T600 50 T900 50 T1200 50 T1500 50 T1800 50 V90 H0Z">
    <animateTransform attributeName="transform" type="translate" dur="9s" repeatCount="indefinite" values="0 0;-600 0"/>
  </path>
  <path fill="url(#g)" opacity=".75" d="M0 60 Q150 30 300 60 T600 60 T900 60 T1200 60 T1500 60 T1800 60 V90 H0Z">
    <animateTransform attributeName="transform" type="translate" dur="6s" repeatCount="indefinite" values="-600 0;0 0"/>
  </path>
</svg>
"""


def waka_svg(data: dict) -> str:
    langs = data["languages"][:LANG_COUNT]
    total = data.get("human_readable_total_including_other_language") or data.get("human_readable_total") or ""
    w, top, row_h = 1200, 104, 46
    h = top + row_h * len(langs) + 22
    track_x, track_w = 300, 520
    peak = max(float(l.get("percent") or 0) for l in langs) or 1
    body = '  <text x="60" y="62" class="t">Coding activity</text>\n'
    body += f'  <text x="262" y="62" class="s">all time, tracked by WakaTime</text>\n'
    if total:
        body += f'  <text x="{w - 60}" y="62" text-anchor="end" style="font:700 26px {MONO};fill:url(#accent)">{escape(total)}</text>\n'
    for i, lang in enumerate(langs):
        name = str(lang.get("name", "?"))
        pct = float(lang.get("percent") or 0)
        bw = max(6.0, pct / peak * track_w)
        y = top + i * row_h
        delay = num(0.2 + i * 0.12)
        col = color_for(name)
        body += (
            f'  <circle cx="68" cy="{y + 9}" r="6" fill="{col}"/>'
            f'<text x="86" y="{y + 15}" class="b">{escape(name)}</text>\n'
            f'  <rect x="{track_x}" y="{y + 3}" width="{track_w}" height="12" rx="6" fill="#ffffff" fill-opacity=".07"/>\n'
            f'  <rect x="{track_x}" y="{y + 3}" width="0" height="12" rx="6" fill="{col}">'
            f'<animate attributeName="width" begin="{delay}s" dur="1.1s" from="0" to="{num(bw)}" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 .8 .2 1"/></rect>\n'
            f'  <text x="{track_x + track_w + 28}" y="{y + 15}" class="m">{escape(str(lang.get("text", "")))}</text>\n'
            f'  <text x="{w - 60}" y="{y + 15}" text-anchor="end" class="b">{pct:.2f}%</text>\n'
        )
    return card(w, h, body, label="Coding activity by language: " + ", ".join(
        f"{l.get('name')} {float(l.get('percent') or 0):.1f}%" for l in langs))


def stats_svg(tiles: list) -> str:
    w, h = 1200, 170
    tw = (w - 120) / len(tiles)
    body = ""
    for i, (value, label) in enumerate(tiles):
        cx = 60 + tw * i + tw / 2
        delay = num(0.2 + i * 0.15)
        body += (
            f'  <g opacity="0"><animate attributeName="opacity" begin="{delay}s" dur="0.6s" from="0" to="1" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" begin="{delay}s" dur="0.6s" from="0 14" to="0 0" fill="freeze"/>'
            f'<text x="{num(cx)}" y="86" text-anchor="middle" style="font:700 46px {SANS};fill:url(#accent)">{escape(value)}</text>'
            f'<text x="{num(cx)}" y="122" text-anchor="middle" class="k">{escape(label.upper())}</text></g>\n'
        )
        if i:
            body += f'  <rect x="{num(60 + tw * i)}" y="50" width="1" height="72" fill="#ffffff" opacity=".1"/>\n'
    return card(w, h, body, label=", ".join(f"{v} {l}" for v, l in tiles), blobs=False)


def wrap(text: str, width: int, max_lines: int) -> list:
    lines, cur = [], ""
    for word in text.split():
        if len(cur) + len(word) + 1 > width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][: width - 1].rstrip() + "…"
    return lines


def project_svg(repo: dict) -> str:
    w, h = 590, 190
    name = repo["name"].replace("_", " ").replace("-", " ")
    desc = (repo.get("description") or "").strip().rstrip('"') or "Open-source project"
    lang = repo.get("language") or "Docs"
    col = color_for(lang)
    body = f'  <text x="32" y="50" class="t" style="font-size:23px">{escape(name)}</text>\n'
    for i, line in enumerate(wrap(desc, 52, 2)):
        body += f'  <text x="32" y="{86 + i * 26}" class="s" style="font-size:17px">{escape(line)}</text>\n'
    body += (
        f'  <circle cx="38" cy="158" r="6" fill="{col}"><animate attributeName="opacity" dur="3s" repeatCount="indefinite" values="1;.4;1"/></circle>'
        f'<text x="52" y="164" class="m" style="font-size:15px">{escape(lang)}</text>\n'
        f'  <text x="{w - 32}" y="164" text-anchor="end" class="m" style="font-size:15px">'
        f'<tspan fill="#f5c542">★</tspan> {repo.get("stargazers_count", 0)}   ⑂ {repo.get("forks_count", 0)}</text>\n'
    )
    return card(w, h, body, label=f"{name}: {desc}", blobs=False)


# ---------------------------------------------------------------- live data


def get_json(url: str, headers: dict):
    req = urllib.request.Request(url, headers={"User-Agent": f"{USER}-profile-readme/1.0", "Accept": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.load(resp)
        if resp.status == 202:
            raise TimeoutError("still being calculated (202)")
        return body


def retry(fn, what: str):
    """Returns fn() or None after 3 temporary failures. Config errors (4xx) abort the run."""
    err = ""
    for attempt in range(3):
        try:
            return fn()
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:300]
            err = f"{what} error {e.code} {e.reason}: {detail}"
            if e.code < 500 and e.code not in (403, 429) or (e.code == 403 and "wakatime" in what.lower()):
                sys.exit(err)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError) as e:
            err = f"{what} request failed: {e}"
        print(f"Attempt {attempt + 1} failed: {err}")
        time.sleep(20)
    print(f"::warning::{err} - keeping the existing card, will retry on next schedule")
    return None


def fetch_waka():
    data = retry(lambda: get_json(f"https://wakatime.com/api/v1/users/{USER}/stats/{WAKA_RANGE}", {})["data"], "WakaTime")
    if data is not None and not data.get("languages"):
        if data.get("is_up_to_date") is False:
            print("::warning::WakaTime stats are still updating - keeping the existing card")
            return None
        sys.exit("WakaTime returned no languages. Turn on 'Display languages publicly' at https://wakatime.com/settings/profile")
    return data


def fetch_github():
    token = os.environ.get("GH_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    def load():
        user = get_json(f"https://api.github.com/users/{USER}", headers)
        repos, page = [], 1
        while True:
            chunk = get_json(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&page={page}", headers)
            repos += chunk
            if len(chunk) < 100:
                break
            page += 1
        return {"user": user, "repos": [r for r in repos if not r.get("private")]}

    return retry(load, "GitHub API")


def hours_tile(waka: dict):
    secs = waka.get("total_seconds_including_other_language") or waka.get("total_seconds")
    if secs:
        return (f"{int(secs // 3600):,}+", "Hours coded")
    text = waka.get("human_readable_total_including_other_language") or waka.get("human_readable_total") or ""
    return (text.split(" hrs")[0] + "+", "Hours coded") if " hrs" in text else None


def build(waka, github, out=OUT):
    """Returns {relative path: svg}. Live cards are skipped when their data is None."""
    files = {
        "header.svg": header_svg(),
        "stack.svg": stack_svg(),
        "footer.svg": footer_svg(),
    }
    tiles = []
    if waka:
        files["waka.svg"] = waka_svg(waka)
        tile = hours_tile(waka)
        if tile:
            tiles.append(tile)
    if github:
        repos = github["repos"]
        own = [r for r in repos if not r.get("fork")]
        tiles.append((f"{len(repos)}", "Public repos"))
        tiles.append((f"{sum(r.get('stargazers_count', 0) for r in own)}", "Stars earned"))
        followers = (github.get("user") or {}).get("followers")
        if followers is not None:
            tiles.append((f"{followers}", "Followers"))
        by_name = {r["name"]: r for r in repos}
        for name in FEATURED:
            if name in by_name:
                files[f"project-{name}.svg"] = project_svg(by_name[name])
    if waka and github:
        files["stats.svg"] = stats_svg(tiles)
    os.makedirs(out, exist_ok=True)
    for name, svg in files.items():
        with open(os.path.join(out, name), "w", encoding="utf-8") as f:
            f.write(svg)
    return sorted(files)


if __name__ == "__main__":
    print("Wrote:", ", ".join(build(fetch_waka(), fetch_github())))
