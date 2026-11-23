#!/usr/bin/env python3
"""Check Android Simplified Chinese resource coverage and placeholders."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MODULES = ("app", "plugins", "plugins/realvnc", "plugins/rustdesk")
FORMAT = re.compile(r"%(?:\d+\$)?[a-zA-Z]")

def tokens(node):
    return sorted(FORMAT.findall("".join(node.itertext())))

def resources(path):
    result = {}
    for node in ET.parse(path).getroot():
        if node.tag not in ("string", "plurals"):
            continue
        key = (node.tag, node.attrib["name"])
        assert key not in result, f"Duplicate resource {key}: {path}"
        result[key] = node
    return result

total = 0
for module in MODULES:
    res = ROOT / module / "src/main/res"
    names = ["strings.xml"] + (["dynamic_strings.xml"] if module == "app" else [])
    for filename in names:
        en = resources(res / "values" / filename)
        zh = resources(res / "values-zh-rCN" / filename)
        assert en.keys() == zh.keys(), f"Missing/extra resource keys in {module}/{filename}: {en.keys() ^ zh.keys()}"
        for key, original in en.items():
            translated = zh[key]
            if key[0] == "plurals":
                source_items = {i.attrib["quantity"]: i for i in original}
                target_items = {i.attrib["quantity"]: i for i in translated}
                assert source_items.keys() == target_items.keys(), key
                for quantity, source in source_items.items():
                    assert tokens(source) == tokens(target_items[quantity]), (key, quantity)
            elif original.attrib.get("formatted") != "false":
                assert tokens(original) == tokens(translated), key
            assert "".join(translated.itertext()).strip(), f"Empty translation: {key}"
        total += len(en)
        print(f"{module}/{filename}: {len(en)} resources verified")
dynamic = resources(ROOT / "app/src/main/res/values/dynamic_strings.xml")
helper = (ROOT / "app/src/main/java/net/pgaskin/remotedesktop/UiText.java").read_text()
assert {k[1] for k in dynamic} == set(re.findall(r"R\.string\.(ui_text_[a-f0-9]+)", helper))
print(f"PASS: {total} resource entries; UI adapter coverage verified")
