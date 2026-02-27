#!/usr/bin/env python3
import datetime as dt
import difflib
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request

API_URL = "https://admin.bgwiedikon.ch/api"
STATE_FILE = "state.json"
DIFF_FILE = "last_change.diff"
EMAIL_BODY_FILE = "email_body.txt"

QUERY = """
query {
  entries(section: "pages", slug: "vermietungen") {
    ... on pages_pages_Entry {
      id
      title
      slug
      intro
      introSmall
      accordionSection {
        __typename
        ... on accordionSection_accordionTitle_BlockType {
          id
          accordionTitle
        }
        ... on accordionSection_accordionText_BlockType {
          id
          accordionText
          nrCols
        }
        ... on accordionSection_documents_BlockType {
          id
          documents {
            title
            url
            extension
            size
            mimeType
          }
        }
        ... on accordionSection_accordionImage_BlockType {
          id
          accordionImage {
            title
            url
          }
        }
      }
    }
  }
}
""".strip()


def http_post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body)


def canonicalize(entry):
    sections = []
    for block in entry.get("accordionSection", []):
        t = block.get("__typename")
        if t == "accordionSection_accordionTitle_BlockType":
            sections.append({"type": "title", "title": block.get("accordionTitle")})
        elif t == "accordionSection_accordionText_BlockType":
            sections.append(
                {
                    "type": "text",
                    "text": block.get("accordionText"),
                    "nrCols": bool(block.get("nrCols")),
                }
            )
        elif t == "accordionSection_documents_BlockType":
            docs = []
            for d in block.get("documents", []) or []:
                docs.append(
                    {
                        "title": d.get("title"),
                        "url": d.get("url"),
                        "extension": d.get("extension"),
                        "size": d.get("size"),
                        "mimeType": d.get("mimeType"),
                    }
                )
            docs.sort(key=lambda x: (x.get("url") or "", x.get("title") or ""))
            sections.append({"type": "documents", "documents": docs})
        elif t == "accordionSection_accordionImage_BlockType":
            imgs = []
            for i in block.get("accordionImage", []) or []:
                imgs.append({"title": i.get("title"), "url": i.get("url")})
            imgs.sort(key=lambda x: (x.get("url") or "", x.get("title") or ""))
            sections.append({"type": "images", "images": imgs})
        else:
            sections.append({"type": t or "unknown", "raw": block})

    return {
        "title": entry.get("title"),
        "slug": entry.get("slug"),
        "intro": entry.get("intro"),
        "introSmall": entry.get("introSmall"),
        "accordionSection": sections,
    }


def payload_hash(payload):
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def load_state(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(path, state):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_diff(old_payload, new_payload):
    old_text = json.dumps(old_payload, ensure_ascii=False, indent=2, sort_keys=True).splitlines()
    new_text = json.dumps(new_payload, ensure_ascii=False, indent=2, sort_keys=True).splitlines()
    diff = list(
        difflib.unified_diff(
            old_text,
            new_text,
            fromfile="previous",
            tofile="current",
            lineterm="",
            n=3,
        )
    )
    if not diff:
        diff = ["No textual diff available."]
    with open(DIFF_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(diff[:800]))
        f.write("\n")


def write_email_body(old_hash, new_hash):
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    lines = [
        "Change detected on https://bgwiedikon.ch/vermietungen",
        "",
        f"Detected at (UTC): {ts}",
        f"Old hash: {old_hash}",
        f"New hash: {new_hash}",
        "",
        "A diff was committed to this repository in last_change.diff.",
    ]
    with open(EMAIL_BODY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    try:
        response = http_post_json(API_URL, {"query": QUERY})
    except urllib.error.URLError as e:
        print(f"ERROR: request failed: {e}", file=sys.stderr)
        return 1

    errors = response.get("errors")
    if errors:
        print(f"ERROR: GraphQL errors: {errors}", file=sys.stderr)
        return 1

    entries = (((response.get("data") or {}).get("entries")) or [])
    if not entries:
        print("ERROR: no entry found for slug 'vermietungen'", file=sys.stderr)
        return 1

    current_payload = canonicalize(entries[0])
    current_hash = payload_hash(current_payload)

    state = load_state(STATE_FILE)
    previous_hash = state.get("hash")
    previous_payload = state.get("payload")

    now = dt.datetime.now(dt.timezone.utc).isoformat()

    if not previous_hash or not previous_payload:
        new_state = {
            "hash": current_hash,
            "updated_at": now,
            "payload": current_payload,
        }
        save_state(STATE_FILE, new_state)
        print("Baseline initialized.")
        return 3

    if previous_hash == current_hash:
        print("No changes detected.")
        return 0

    write_diff(previous_payload, current_payload)
    write_email_body(previous_hash, current_hash)

    new_state = {
        "hash": current_hash,
        "updated_at": now,
        "payload": current_payload,
    }
    save_state(STATE_FILE, new_state)

    print("Change detected.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
