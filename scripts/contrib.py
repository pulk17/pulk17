#!/usr/bin/env python3
"""Keeps the "Open source" table in README.md in sync with GitHub.

Finds every PR the user opened in repos they don't own, keeps the ones from
approved projects (contrib.yml), and rewrites the block between
<!-- contrib:start --> and <!-- contrib:end -->.

    python scripts/contrib.py                         # refresh
    python scripts/contrib.py --action hide    --target https://github.com/o/r/pull/1
    python scripts/contrib.py --action unhide  --target https://github.com/o/r/pull/1
    python scripts/contrib.py --action hide    --target owner/repo     # a whole repo
    python scripts/contrib.py --action approve --target owner/repo [--name "Shown name"]

hide / unhide / approve are saved to contrib.state.json, so contrib.yml stays
exactly as you wrote it. Needs GITHUB_TOKEN in the environment (the workflow
passes its own); without one, GitHub allows ~10 searches a minute.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "contrib.yml")
STATE = os.path.join(ROOT, "contrib.state.json")
README = os.path.join(ROOT, "README.md")
START, END = "<!-- contrib:start -->", "<!-- contrib:end -->"
MAX_LINES = 4  # PRs listed per project before "+N more"
PR_URL = re.compile(r"^https://github\.com/([^/]+/[^/]+)/pull/(\d+)/?$")
REPO = re.compile(r"^(?:https://github\.com/)?([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/?$")


# ---------------------------------------------------------------- GitHub API
def api(path):
    req = urllib.request.Request("https://api.github.com" + path, headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "contrib-readme",
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_prs(user):
    q = urllib.parse.quote(f"author:{user} type:pr -user:{user}")
    items, page = [], 1
    while True:
        d = api(f"/search/issues?q={q}&per_page=100&page={page}")
        if d.get("incomplete_results"):
            sys.exit("GitHub returned incomplete search results; not touching the README.")
        items += d["items"]
        if len(items) >= d["total_count"] or not d["items"] or page == 10:
            return items
        page += 1


def fetch_stars(repos):
    return {r: api(f"/repos/{r}")["stargazers_count"] for r in repos}


# ---------------------------------------------------------------- state
def load_state():
    s = {"hidden_prs": [], "hidden_repos": [], "approved": {}, "pending": {}}
    if os.path.exists(STATE):
        with open(STATE) as f:
            s.update(json.load(f))
    return s


def save_state(s):
    s = {k: (sorted(set(v)) if isinstance(v, list) else dict(sorted(v.items()))) for k, v in s.items()}
    with open(STATE, "w") as f:
        json.dump(s, f, indent=2, ensure_ascii=False)
        f.write("\n")


def apply_action(state, action, target, name):
    target = (target or "").strip()
    pr, repo = PR_URL.match(target), REPO.match(target)
    if action == "refresh":
        return
    if not (pr or repo):
        sys.exit(f"--target must be a PR link or owner/repo, got {target!r}")
    if action == "hide":
        (state["hidden_prs"] if pr else state["hidden_repos"]).append(target.rstrip("/") if pr else repo.group(1))
    elif action == "unhide":
        if pr:
            state["hidden_prs"] = [u for u in state["hidden_prs"] if u != target.rstrip("/")]
        else:
            state["hidden_repos"] = [r for r in state["hidden_repos"] if r.lower() != repo.group(1).lower()]
    elif action == "approve":
        r = pr.group(1) if pr else repo.group(1)
        state["approved"][r] = name.strip() if name and name.strip() else r.split("/")[1]
        state["pending"].pop(r, None)
    else:
        sys.exit(f"unknown action {action!r}")


# ---------------------------------------------------------------- model
TAG = re.compile(r"^\s*(\[[^\]]*\]\s*[-:]?\s*)+")          # "[FIX] : ", "[Feature] - "
CONV = re.compile(r"^\s*[a-z]+(\([^)]*\))?!?:\s+")         # "fix(ts): ", "imgproc: "


def clean_title(t):
    t = CONV.sub("", TAG.sub("", t)).strip().rstrip(".")
    return t[:1].upper() + t[1:]


def build_projects(cfg, state, items):
    owner_hidden = {o.lower() for o in cfg.get("hidden_owners", [])}
    repo_hidden = {r.lower() for r in state["hidden_repos"]}
    pr_hidden = set(state["hidden_prs"])
    titles = cfg.get("titles", {}) or {}

    projects, repo_to_project = [], {}
    for p in cfg.get("projects", []):
        proj = dict(name=p["name"], repos=list(p["repos"]), note=p.get("note"), summary=p.get("summary"), prs=[])
        projects.append(proj)
        for r in p["repos"]:
            repo_to_project[r.lower()] = proj
    for r, name in state["approved"].items():
        if r.lower() in repo_to_project:
            continue
        proj = next((p for p in projects if p["name"] == name), None)
        if proj is None:
            proj = dict(name=name, repos=[], note=None, summary=None, prs=[])
            projects.append(proj)
        proj["repos"].append(r)
        repo_to_project[r.lower()] = proj

    pending = {}
    for it in items:
        repo = it["repository_url"].split("/repos/")[1]
        url = it["html_url"]
        merged = (it.get("pull_request") or {}).get("merged_at")
        status = "merged" if merged else ("open" if it["state"] == "open" else "closed")
        if (repo.split("/")[0].lower() in owner_hidden or repo.lower() in repo_hidden or url in pr_hidden
                or (status == "closed" and cfg.get("hide_closed_unmerged", True))):
            continue
        proj = repo_to_project.get(repo.lower())
        if proj is None:
            pending[repo] = pending.get(repo, 0) + 1
            continue
        proj["prs"].append(dict(
            repo=repo, number=it["number"], url=url, status=status,
            title=titles.get(url) or clean_title(it["title"]),
            when=merged or it.get("closed_at") or it["created_at"],
        ))
    state["pending"] = pending
    return [p for p in projects if p["prs"]]


# ---------------------------------------------------------------- render
def stars_label(n):
    if n >= 1000:
        return f"{n / 1000:.1f}k stars".replace(".0k", "k")
    return f"{n} star" + ("" if n == 1 else "s")


def md(s):
    return s.replace("|", "\\|")


def join_names(names):
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def render(user, projects, stars):
    for p in projects:
        p["stars"] = max(stars.get(r, 0) for r in p["repos"] if any(x["repo"] == r for x in p["prs"]))
        p["merged"] = sum(x["status"] == "merged" for x in p["prs"])
        p["open"] = sum(x["status"] == "open" for x in p["prs"])
        p["prs"].sort(key=lambda x: x["when"], reverse=True)   # newest first,
        p["prs"].sort(key=lambda x: x["status"] != "merged")   # merged ones on top
    projects.sort(key=lambda p: (p["merged"] == 0, -p["stars"]))

    # A project counts as "merged into" only if a PR landed in its main repo
    # (the first one listed); otherwise the sentence names the exact repo.
    merged_in = []
    for p in projects:
        if any(x["status"] == "merged" and x["repo"] == p["repos"][0] for x in p["prs"]):
            merged_in.append(p["name"])
        else:
            merged_in += sorted({x["repo"] for x in p["prs"] if x["status"] == "merged"})
    review_in = [p["name"] for p in projects
                 if any(x["status"] == "open" and x["repo"] == p["repos"][0] for x in p["prs"]) and p["name"] not in merged_in]
    lead = []
    if merged_in:
        lead.append(f"Merged into {join_names(merged_in)}.")
    if review_in:
        lead.append(f"In review at {join_names(review_in)}.")

    rows = ["| Project | Contributions |", "| :-- | :-- |"]
    for p in projects:
        main = next(r for r in p["repos"] if any(x["repo"] == r for x in p["prs"]))
        counts = []
        if p["merged"]:
            counts.append(f"{p['merged']} merged")
        if p["open"]:
            counts.append(f"{p['open']} in review")
        left = f"**[{md(p['name'])}](https://github.com/{main})**<br><sub>{stars_label(p['stars'])}</sub>"
        if p["summary"]:
            lists = " ".join(
                f"[{'all PRs' if len(p['repos']) == 1 else r.split('/')[1]}](https://github.com/{r}/pulls?q=is%3Apr+author%3A{user})"
                for r in p["repos"] if any(x["repo"] == r for x in p["prs"]))
            right = f"{md(p['summary'])}<br><sub>{', '.join(counts)}&ensp;{lists}</sub>"
        else:
            # PRs outside the project's main repo say where they went, e.g. "boost: ..."
            lines = [f"{'✓' if x['status'] == 'merged' else '○'} "
                     + (f"{x['repo'].split('/')[1]}: " if x["repo"] != p["repos"][0] else "")
                     + f"[{md(x['title'])}]({x['url']})"
                     for x in p["prs"][:MAX_LINES]]
            extra = len(p["prs"]) - MAX_LINES
            if extra > 0:
                lines.append(f"<sub>[+{extra} more](https://github.com/{main}/pulls?q=is%3Apr+author%3A{user})</sub>")
            if p["note"]:
                lines.append(f"<sub>{md(p['note'])}</sub>")
            right = "<br>".join(lines)
        rows.append(f"| {left} | {right} |")

    latest = max(x["when"] for p in projects for x in p["prs"])
    day = dt.datetime.fromisoformat(latest.replace("Z", "+00:00")).strftime("%-d %b %Y")
    foot = f"<sub>✓ merged&emsp;○ in review&emsp;Kept up to date from GitHub by a scheduled workflow. Latest activity {day}.</sub>"
    return "\n".join([START, " ".join(lead), "", *rows, "", foot, END])


def write_readme(block, path=README):
    with open(path) as f:
        text = f.read()
    if START not in text or END not in text:
        sys.exit(f"{path} has no {START} ... {END} block")
    new = text[: text.index(START)] + block + text[text.index(END) + len(END):]
    if new != text:
        with open(path, "w") as f:
            f.write(new)
    return new != text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--action", default="refresh", choices=["refresh", "hide", "unhide", "approve"])
    ap.add_argument("--target", default="")
    ap.add_argument("--name", default="")
    ap.add_argument("--fixture", help="search API JSON to use instead of calling GitHub")
    ap.add_argument("--stars-fixture", help="{repo: stars} JSON to use instead of calling GitHub")
    ap.add_argument("--readme", default=README)
    a = ap.parse_args()

    with open(CONFIG) as f:
        cfg = yaml.safe_load(f)
    state = load_state()
    apply_action(state, a.action, a.target, a.name)

    if a.fixture:
        with open(a.fixture) as f:
            items = json.load(f)["items"]
    else:
        items = fetch_prs(cfg["user"])
    projects = build_projects(cfg, state, items)
    if not projects:
        sys.exit("No approved contributions found; not touching the README.")
    shown = sorted({x["repo"] for p in projects for x in p["prs"]})
    if a.stars_fixture:
        with open(a.stars_fixture) as f:
            stars = json.load(f)
    else:
        stars = fetch_stars(shown)

    changed = write_readme(render(cfg["user"], projects, stars), a.readme)
    save_state(state)
    total = sum(len(p["prs"]) for p in projects)
    print(f"{total} PRs across {len(projects)} projects shown; README {'updated' if changed else 'unchanged'}.")
    if state["pending"]:
        print("Waiting for approval: " + ", ".join(f"{r} ({n})" for r, n in state["pending"].items()))


if __name__ == "__main__":
    main()
