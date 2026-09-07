FIG1 = '''<svg viewBox="0 0 780 320" role="img" aria-label="3案それぞれで、参照が節を指すときの鍵が何になり、節の名前や位置が変わったときに結びがどうなるか">
<defs>
 <marker id="i1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="var(--key)"/></marker>
 <marker id="i2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="var(--add)"/></marker>
 <marker id="i3" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="var(--out)"/></marker>
</defs>
<text x="8" y="16" font-size="11" fill="var(--muted)">A　節に、変わらない印</text>
<rect x="8" y="30" width="228" height="38" fill="none" stroke="currentColor" stroke-width="1.3"/>
<text x="122" y="54" text-anchor="middle" font-size="12" fill="currentColor">指す側の節（参照）</text>
<line x1="122" y1="68" x2="122" y2="108" stroke="var(--key)" stroke-width="1.8" marker-end="url(#i1)"/>
<text x="132" y="92" font-size="11.5" font-weight="700" fill="var(--key)">SC-01J7Q4K</text>
<rect x="8" y="114" width="228" height="52" fill="none" stroke="var(--key)" stroke-width="1.9"/>
<text x="122" y="134" text-anchor="middle" font-size="11.5" font-weight="700" fill="var(--key)">SC-01J7Q4K</text>
<text x="122" y="152" text-anchor="middle" font-size="11" fill="var(--muted)">「予約を確定する」</text>
<text x="8" y="196" font-size="11" fill="var(--muted)">名前を直す ／ 別の親へ移す</text>
<rect x="8" y="206" width="228" height="46" fill="none" stroke="var(--key)" stroke-width="1.9"/>
<text x="122" y="225" text-anchor="middle" font-size="11.5" font-weight="700" fill="var(--key)">SC-01J7Q4K</text>
<text x="122" y="242" text-anchor="middle" font-size="11" fill="var(--add)">「予約を確定できる」</text>
<text x="8" y="278" font-size="12" font-weight="700" fill="var(--key)">結びは残る（moved 1）</text>
<text x="8" y="298" font-size="11" fill="var(--muted)">名前は表示になる。印を採番</text>
<text x="8" y="314" font-size="11" fill="var(--muted)">できるのは道具だけになる</text>

<line x1="256" y1="8" x2="256" y2="314" stroke="var(--rule)" stroke-width="1"/>

<text x="276" y="16" font-size="11" fill="var(--muted)">B　位置＋移行の宣言</text>
<rect x="276" y="30" width="228" height="38" fill="none" stroke="currentColor" stroke-width="1.3"/>
<text x="390" y="54" text-anchor="middle" font-size="12" fill="currentColor">指す側の節（参照）</text>
<line x1="390" y1="68" x2="390" y2="108" stroke="currentColor" stroke-width="1.6" marker-end="url(#i1)"/>
<text x="400" y="92" font-size="11.5" font-weight="700" fill="currentColor">doc-7 / §2 / 3番目</text>
<rect x="276" y="114" width="228" height="52" fill="none" stroke="currentColor" stroke-width="1.6"/>
<text x="390" y="134" text-anchor="middle" font-size="11.5" fill="currentColor">doc-7 / §2 / 3番目</text>
<text x="390" y="152" text-anchor="middle" font-size="11" fill="var(--muted)">「予約を確定する」</text>
<text x="276" y="196" font-size="11" fill="var(--muted)">名前を直す ／ 別の親へ移す</text>
<rect x="276" y="206" width="228" height="46" fill="none" stroke="var(--add)" stroke-width="1.9"/>
<text x="390" y="225" text-anchor="middle" font-size="11.5" font-weight="700" fill="var(--add)">doc-7 / §4 / 1番目</text>
<text x="390" y="242" text-anchor="middle" font-size="11" fill="var(--muted)">位置が変わった</text>
<line x1="390" y1="252" x2="390" y2="262" stroke="var(--add)" stroke-width="1.6" marker-end="url(#i2)"/>
<text x="276" y="278" font-size="12" font-weight="700" fill="var(--add)">宣言が在れば残り、無ければ切れる</text>
<text x="276" y="298" font-size="11" fill="var(--muted)">そして「書き忘れた」ことは、</text>
<text x="276" y="314" font-size="11" fill="var(--muted)">どこにも現れない</text>

<line x1="524" y1="8" x2="524" y2="314" stroke="var(--rule)" stroke-width="1"/>

<text x="544" y="16" font-size="11" fill="var(--muted)">C　参照の側に、解決状態</text>
<rect x="544" y="30" width="228" height="38" fill="none" stroke="var(--out)" stroke-width="1.6"/>
<text x="658" y="48" text-anchor="middle" font-size="12" fill="currentColor">指す側の節（参照）</text>
<text x="658" y="63" text-anchor="middle" font-size="10.5" fill="var(--out)">状態：届いた／届かない／外部／確かめない</text>
<line x1="658" y1="68" x2="658" y2="108" stroke="var(--out)" stroke-width="1.6" stroke-dasharray="5 4" marker-end="url(#i3)"/>
<text x="668" y="92" font-size="11.5" fill="var(--out)">鍵は名前のまま</text>
<rect x="544" y="114" width="228" height="52" fill="none" stroke="currentColor" stroke-width="1.6"/>
<text x="658" y="140" text-anchor="middle" font-size="11.5" fill="currentColor">「予約を確定する」</text>
<text x="544" y="196" font-size="11" fill="var(--muted)">名前を直す ／ 別の親へ移す</text>
<rect x="544" y="206" width="228" height="46" fill="none" stroke="var(--out)" stroke-width="1.6" stroke-dasharray="5 4"/>
<text x="658" y="232" text-anchor="middle" font-size="11.5" fill="var(--add)">届かない</text>
<text x="544" y="278" font-size="12" font-weight="700" fill="var(--out)">届かないことは分かる</text>
<text x="544" y="298" font-size="11" fill="var(--muted)">「移った」のか「消えた」のかは</text>
<text x="544" y="314" font-size="11" fill="var(--muted)">分からない。人が毎回決める</text>
</svg>'''

FIG2 = '''<svg viewBox="0 0 780 300" role="img" aria-label="3案それぞれで、段1と段2のどちらに何が増えるか。案Aは段1だけが増え、案Bは両方が増え、案Cは段1が1つ増える">
<text x="150" y="18" text-anchor="middle" font-size="11.5" font-weight="700" fill="var(--muted)">段1　全型が継ぐ契約</text>
<text x="530" y="18" text-anchor="middle" font-size="11.5" font-weight="700" fill="var(--muted)">段2　8つの型</text>
<line x1="8" y1="26" x2="772" y2="26" stroke="var(--rule)"/>

<text x="8" y="58" font-size="12" font-weight="700" fill="var(--key)">A</text>
<rect x="28" y="38" width="244" height="62" fill="none" stroke="var(--key)" stroke-width="1.9"/>
<text x="40" y="56" font-size="11" fill="var(--key)">・節が印を持つ／採番と不変</text>
<text x="40" y="74" font-size="11" fill="var(--key)">・参照は印を指す</text>
<text x="40" y="92" font-size="11" fill="var(--key)">・人が読む射影では印を落とす</text>
<rect x="408" y="38" width="244" height="62" fill="none" stroke="var(--rule)" stroke-width="1.4"/>
<text x="530" y="66" text-anchor="middle" font-size="12" font-weight="700" fill="var(--muted)">増えない</text>
<text x="530" y="86" text-anchor="middle" font-size="10.5" fill="var(--muted)">既にある document への後付けの発番だけ</text>
<text x="668" y="74" font-size="11" fill="var(--key)">← いま動いている段</text>

<text x="8" y="150" font-size="12" font-weight="700" fill="var(--add)">B</text>
<rect x="28" y="118" width="244" height="70" fill="none" stroke="var(--add)" stroke-width="1.9"/>
<text x="40" y="138" font-size="11" fill="var(--add)">・移行の操作を動詞として固定</text>
<text x="40" y="156" font-size="11" fill="var(--add)">　（改名・移動・親の付け替え・型変更）</text>
<text x="40" y="178" font-size="11" font-weight="700" fill="var(--add)">型が増えるほど、ここが太る</text>
<rect x="408" y="118" width="244" height="70" fill="none" stroke="var(--add)" stroke-width="1.9"/>
<text x="420" y="140" font-size="11" fill="var(--add)">・各型が、自分の位置の安定を守る</text>
<text x="420" y="162" font-size="11" fill="var(--add)">・アドレスが動くたび、それを指す</text>
<text x="420" y="180" font-size="11" fill="var(--add)">　参照が全部書き換わる</text>
<text x="286" y="158" font-size="10.5" fill="var(--add)">論点6を</text>
<text x="286" y="174" font-size="10.5" fill="var(--add)">案A側へ寄せる</text>

<text x="8" y="238" font-size="12" font-weight="700" fill="var(--out)">C</text>
<rect x="28" y="212" width="244" height="56" fill="none" stroke="var(--out)" stroke-width="1.6"/>
<text x="40" y="236" font-size="11" fill="var(--out)">・参照の語彙に、型と解決状態</text>
<text x="40" y="256" font-size="11" font-weight="700" fill="var(--out)">同一性は1つも増えない</text>
<rect x="408" y="212" width="244" height="56" fill="none" stroke="var(--out)" stroke-width="1.6"/>
<text x="420" y="236" font-size="11" fill="var(--out)">・各型が、参照の欄で状態を申告</text>
<text x="420" y="256" font-size="11" fill="var(--out)">・区別は付かないまま、人へ残る</text>

<line x1="8" y1="284" x2="772" y2="284" stroke="var(--rule)"/>
<text x="8" y="298" font-size="11" fill="var(--muted)">いま再定義しているのは段2 である。段2 に何も置かない案は A だけで、C は A と重ねて採れる。</text>
</svg>'''
