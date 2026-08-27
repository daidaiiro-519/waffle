"""描いた Markdown を、そのまま見た目にするための最小の変換。
部品が実際に出す構文（見出し・段落・箇条・番号つき・表・字面・強調・行内コード・区切り）だけを扱う。"""
import re, html
def conv(md:str)->str:
    e=html.escape
    def inline(s):
        s=e(s)
        s=re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
        s=re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
        return s
    out=[]; i=0; L=md.split("\n")
    while i<len(L):
        l=L[i]
        if l.startswith("```"):
            lang=l[3:].strip(); body=[]; i+=1
            while i<len(L) and not L[i].startswith("```"): body.append(L[i]); i+=1
            i+=1
            out.append(f'<pre class="mdcode"{f" data-lang={lang}" if lang else ""}>'
                       f'<code>{e(chr(10).join(body))}</code></pre>'); continue
        m=re.match(r'^(#{1,6})\s+(.*)$', l)
        if m:
            n=len(m.group(1)); out.append(f'<h{min(n+1,6)} class="mdh">{inline(m.group(2))}</h{min(n+1,6)}>'); i+=1; continue
        if re.match(r'^\|.*\|$', l) and i+1<len(L) and re.match(r'^\|[-:| ]+\|$', L[i+1]):
            head=[c.strip() for c in l.strip("|").split("|")]; i+=2; rows=[]
            while i<len(L) and re.match(r'^\|.*\|$', L[i]):
                rows.append([c.strip() for c in L[i].strip("|").split("|")]); i+=1
            th="".join(f"<th>{inline(c)}</th>" for c in head)
            tb="".join("<tr>"+"".join(f"<td>{inline(c)}</td>" for c in r)+"</tr>" for r in rows)
            out.append(f'<div class="mdtblwrap"><table class="mdtbl"><thead><tr>{th}</tr></thead>'
                       f'<tbody>{tb}</tbody></table></div>'); continue
        if re.match(r'^\s*[-*]\s+', l):
            items=[]
            while i<len(L) and re.match(r'^\s*[-*]\s+', L[i]):
                items.append(re.sub(r'^\s*[-*]\s+','',L[i])); i+=1
            out.append("<ul class='mdul'>"+"".join(f"<li>{inline(x)}</li>" for x in items)+"</ul>"); continue
        if re.match(r'^\s*\d+\.\s+', l):
            items=[]
            while i<len(L) and re.match(r'^\s*\d+\.\s+', L[i]):
                items.append(re.sub(r'^\s*\d+\.\s+','',L[i])); i+=1
            out.append("<ol class='mdol'>"+"".join(f"<li>{inline(x)}</li>" for x in items)+"</ol>"); continue
        if l.strip()=="---": out.append('<hr class="mdhr">'); i+=1; continue
        if l.strip()=="": i+=1; continue
        buf=[]
        while i<len(L) and L[i].strip() and not re.match(r'^(#{1,6}\s|\||```|\s*[-*]\s|\s*\d+\.\s)', L[i]) and L[i].strip()!="---":
            buf.append(L[i]); i+=1
        out.append(f'<p class="mdp">{inline(" ".join(buf))}</p>')
    return "".join(out)
