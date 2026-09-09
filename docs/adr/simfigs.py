def _b(x,y,w,h,label,stroke,sw=1.3,size=9,ly=None,bold=False,dash=None):
    d=f' stroke-dasharray="{dash}"' if dash else ""
    fw=' font-weight="700"' if bold else ""
    o=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="none" stroke="{stroke}" stroke-width="{sw}"{d}/>'
    if label:
        o+=(f'<text x="{x+w/2}" y="{y+(ly or h/2+3.5)}" text-anchor="middle" font-size="{size}" '
            f'fill="{stroke}"{fw}>{label}</text>')
    return o
def _t(x,y,s,tone="var(--muted)",size=9,anchor=None,bold=False):
    a=f' text-anchor="{anchor}"' if anchor else ""
    fw=' font-weight="700"' if bold else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{tone}"{a}{fw}>{s}</text>'
K,M,D,C="var(--key)","var(--muted)","var(--dim)","currentColor"
AR=('<defs><marker id="sa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
    'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="var(--key)"/></marker></defs>')

AXES = ('<svg viewBox="0 0 660 232" role="img" aria-label="欄で切ると型が縦に増えるが、軸で切ると型は2つのままで値が横に増える">'
 + _t(0,12,"落とした形 ── 欄の集合で切る",D,9.5,bold=True)
 + _b(0,24,168,24,"型：この欄の組",D,1.1,8.5)
 + _b(0,52,168,24,"型：1欄だけ違う組",D,1.1,8.5)
 + _b(0,80,168,24,"型：さらに1欄違う組",D,1.1,8.5)
 + _b(0,108,168,24,"型：…",D,1.1,8.5)
 + _t(84,150,"1欄違うたびに縦に増える",D,8.5,"middle")
 + _t(84,166,"閾値に根拠が持てない",D,8.5,"middle")
 + '<line x1="196" y1="10" x2="196" y2="200" stroke="var(--rule)"/>'
 + _t(224,12,"採る形 ── 軸の集合で切る",K,9.5,bold=True)
 + _b(224,24,436,72,"",K,1.5)
 + _t(240,44,"CodingSchema",K,10,bold=True)
 + _t(240,62,"軸：言語 × アーキ × 用途",M,8.5)
 + _b(240,70,64,18,"Go",C,1,8)
 + _b(310,70,64,18,"Rust",C,1,8)
 + _b(380,70,86,18,"data-port",C,1,8)
 + _b(472,70,86,18,"hook",C,1,8)
 + _t(576,84,"…値が増える",M,8)
 + _b(224,106,436,72,"",K,1.5)
 + _t(240,126,"SpecSchema",K,10,bold=True)
 + _t(240,144,"軸：業務 × 接点 × 基盤",M,8.5)
 + _b(240,152,64,18,"予約",C,1,8)
 + _b(310,152,64,18,"請求",C,1,8)
 + _b(380,152,86,18,"CLI",C,1,8)
 + _b(472,152,86,18,"MCP",C,1,8)
 + _t(576,166,"…値が増える",M,8)
 + _t(224,204,"型は2つのまま。値が増えても、型は増えない",K,9.5,bold=True)
 + '</svg>', '')

PORTS = ('<svg viewBox="0 0 660 296" role="img" aria-label="script が処理を持つ形と、能力1つに差し出し口が3つ付く形">'
 + AR
 + _t(0,12,"落とした形 ── script が処理そのものを持つ",D,9.5,bold=True)
 + _b(0,22,196,48,"",D,1.2)
 + _t(98,40,"Hook の script",D,9,"middle",True)
 + _t(98,56,"確かめる処理を、中に持つ",D,8.5,"middle")
 + _t(216,44,"CLI からも MCP からも呼べない",D,9)
 + _t(216,60,"承認も検証も通らない",D,9)
 + '<line x1="0" y1="90" x2="660" y2="90" stroke="var(--rule)"/>'
 + _t(0,110,"採る形 ── 能力は1つ、差し出し口が3つ",K,9.5,bold=True)
 + _b(170,122,320,46,"",K,1.6)
 + _t(330,142,"ずれを確かめる",K,10,"middle",True)
 + _t(330,158,"能力 ── 業務の層",M,8.5,"middle")
 + f'<line x1="120" y1="216" x2="188" y2="172" stroke="{K}" stroke-width="1.3" marker-end="url(#sa)"/>'
 + f'<line x1="330" y1="216" x2="330" y2="172" stroke="{K}" stroke-width="1.3" marker-end="url(#sa)"/>'
 + f'<line x1="540" y1="216" x2="472" y2="172" stroke="{K}" stroke-width="1.3" marker-end="url(#sa)"/>'
 + _b(40,218,160,44,"",C,1.1)
 + _t(120,236,"CLI の約束",C,9,"middle",True)
 + _t(120,252,"業務 × 接点",M,8,"middle")
 + _b(250,218,160,44,"",C,1.1)
 + _t(330,236,"MCP の約束",C,9,"middle",True)
 + _t(330,252,"業務 × 接点",M,8,"middle")
 + _b(460,218,160,44,"",C,1.1)
 + _t(540,236,"Hook の約束",C,9,"middle",True)
 + _t(540,252,"どの事象で起きるか",M,8,"middle")
 + _t(540,284,"script は呼ぶだけ",K,8.5,"middle",True)
 + '</svg>', '')
