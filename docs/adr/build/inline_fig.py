"""class だけの図に、明色の値を属性として補う。ページのCSSがあればそちらが勝つ。"""
import xml.etree.ElementTree as ET
NS="http://www.w3.org/2000/svg"
F='Noto Sans JP","Hiragino Kaku Gothic ProN",sans-serif'
FONT='"Noto Sans JP", "Hiragino Kaku Gothic ProN", sans-serif'
L=dict(line="#C3CAD2",sym="#79828F",fill="#F5F7F9",stroke="#C3CAD2",
       acc="#16636B",accbg="#E2EFF0",text="#171B23",soft="#4B5563",faint="#79828F")

def _cls(el): return set((el.get("class") or "").split())

def inline(svg:str)->str:
    ET.register_namespace("", NS)
    root=ET.fromstring(svg)
    def walk(el, ancestors):
        c=_cls(el); tag=el.tag.split("}")[-1]
        anc=set().union(*ancestors) if ancestors else set()
        def put(**kw):
            for k,v in kw.items():
                if el.get(k) is None: el.set(k,v)
        if "wf-group" in c and tag=="rect":
            put(fill="none",stroke=L["acc"],**{"stroke-width":"1.1","stroke-dasharray":"5 4"},opacity=".75")
        elif "wf-group-label" in c:
            put(fill=L["acc"],**{"font-size":"10","font-family":FONT})
        elif "wf-edge" in c:
            put(fill="none",stroke=L["line"],**{"stroke-width":"1.2"})
        elif "wf-arrow" in c:
            put(fill=L["line"])
        elif "wf-edge-label" in c:
            put(fill=L["faint"],**{"font-size":"10","font-family":FONT,"text-anchor":"middle"})
        elif "wf-label-bg" in c:
            put(fill=L["fill"],stroke="none")
        elif "wf-end-word" in c:
            put(fill=L["soft"],**{"font-size":"9","font-family":FONT})
        elif "wf-ring" in c:
            put(fill="none",stroke=L["text"],**{"stroke-width":"1.4"})
        elif "wf-node" in anc or "wf-node" in c:
            focus="wf-node--focus" in anc or "wf-node--added" in anc
            muted="wf-node--muted" in anc or "wf-node--removed" in anc
            if tag=="rect":
                if muted: put(fill="none",stroke=L["faint"],**{"stroke-dasharray":"4 3","stroke-width":"1"})
                elif focus: put(fill=L["accbg"],stroke=L["acc"],**{"stroke-width":"1.4"})
                else: put(fill=L["fill"],stroke=L["stroke"],**{"stroke-width":"1"})
            elif tag=="circle":
                put(fill=L["text"],stroke="none")
            elif tag=="text":
                col=L["acc"] if focus else (L["faint"] if muted else L["text"])
                sz="11" if "wf-row" in c else "12"
                put(fill=col,**{"font-size":sz,"font-family":FONT,
                                "text-anchor":"start" if "wf-row" in c else "middle"})
                if focus or "wf-head" in c: put(**{"font-weight":"600"})
        for ch in el: walk(ch, ancestors+[c])
    walk(root,[])
    return ET.tostring(root,encoding="unicode")
