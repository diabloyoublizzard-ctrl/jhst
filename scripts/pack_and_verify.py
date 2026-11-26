import os
import re
import subprocess
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def read(name):
    with open(os.path.join(ROOT, name), "r", encoding="utf-8") as f:
        return f.read()

def write(name, content):
    with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
        f.write(content)

def verify_js_syntax(label, js_code):
    runner = f"""
const code = {json.dumps(js_code)};
try {{
    new Function(code);
    "OK";
}} catch (e) {{
    "ERR: " + e.name + ": " + e.message;
}}
"""
    res = subprocess.run(
        ["/usr/bin/osascript", "-l", "JavaScript", "-"],
        input=runner,
        text=True,
        capture_output=True
    )
    out = (res.stdout or "").strip()
    err = (res.stderr or "").strip()
    if res.returncode != 0 or out != "OK":
        raise RuntimeError(f"[{label}] JS syntax check failed: rc={res.returncode}, out={out!r}, err={err!r}")
    print(f"OK: {label} ({len(js_code)} chars)")

def extract_inline_scripts(html):
    scripts = []
    for m in re.finditer(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, flags=re.S | re.I):
        code = m.group(1).strip()
        if code:
            scripts.append(code)
    return scripts

def main():
    index_html = read("index.html")
    data_js = read("data.js")
    patches_js = read("patches.js")

    if "202611151953" in index_html or "2026.11.15.1953" in index_html:
        raise RuntimeError("Found leftover 202611151953 version string in index.html")

    mobile_html = re.sub(
        r'<script src="data\.js[^"]*"></script>',
        lambda _: f"<script>\n{data_js}\n</script>",
        index_html,
        count=1
    )
    mobile_html = re.sub(
        r'<script src="patches\.js[^"]*"></script>',
        lambda _: f"<script>\n{patches_js}\n</script>",
        mobile_html,
        count=1
    )

    if mobile_html == index_html:
        raise RuntimeError("Failed to inline data.js or patches.js into jhst_mobile.html")

    write("jhst_mobile.html", mobile_html)
    print(f"Packed jhst_mobile.html ({len(mobile_html)} chars)")

    verify_js_syntax("data.js", data_js)
    verify_js_syntax("patches.js", patches_js)

    idx_scripts = extract_inline_scripts(index_html)
    print(f"Found {len(idx_scripts)} inline scripts in index.html")
    for i, sc in enumerate(idx_scripts):
        verify_js_syntax(f"index.html script#{i+1}", sc)

    mob_scripts = extract_inline_scripts(mobile_html)
    print(f"Found {len(mob_scripts)} inline scripts in jhst_mobile.html")
    for i, sc in enumerate(mob_scripts):
        verify_js_syntax(f"jhst_mobile.html script#{i+1}", sc)

    print("ALL JS SYNTAX CHECKS PASSED")

if __name__ == "__main__":
    main()
