import hashlib, pathlib, sys
from playwright.sync_api import sync_playwright

JS = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
SRC = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")
PAGE = f'<!doctype html><meta charset="utf-8"><script>{JS}</script><body></body>'

def bake(font):
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chromium-headless-shell")
        pg = b.new_page()
        pg.set_content(PAGE, wait_until="load")
        svg = pg.evaluate("""async ([src, font]) => {
            mermaid.initialize({startOnLoad:false, securityLevel:'strict',
                                theme:'base', themeVariables:{fontFamily: font}});
            const {svg} = await mermaid.render('baked', src);
            return svg; }""", [SRC, font])
        b.close()
    return svg

a, b_ = bake("Noto Sans JP, sans-serif"), bake("Noto Sans JP, sans-serif")
c = bake("serif")
h = lambda s: hashlib.sha256(s.encode()).hexdigest()[:12]
print(f"  同じ条件で2回      : {h(a)}  {h(b_)}   → {'一致' if a == b_ else '不一致'}")
print(f"  書体だけ変えた     : {h(c)}          → {'一致' if a == c else '不一致'}")