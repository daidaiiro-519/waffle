"""Semantic SVG diagrams for the workshop slides; no external assets."""
from html import escape

INK = '#252b29'
DIM = '#59605a'
LINE = '#a8b09f'
PANEL = '#e9e5da'
PAPER = '#fffaf2'
ACCENT = '#b64326'

def text(x, y, lines, size=22, color=INK, weight=400, anchor='start', gap=None):
    if isinstance(lines, str):
        lines = [lines]
    gap = gap or size*1.55
    return ''.join(f'<text x="{x}" y="{y+i*gap}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{escape(s)}</text>' for i,s in enumerate(lines))

def rect(x,y,w,h,fill=PANEL,r=12,stroke='none'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'

def path(d,color=LINE,width=2,fill='none'):
    return f'<path d="{d}" stroke="{color}" stroke-width="{width}" fill="{fill}" stroke-linecap="round" stroke-linejoin="round"/>'

def arrow(x1,y1,x2,y2,color=LINE):
    tip=f'M{x2-8} {y2-7} l8 7 -8 7' if x2>x1 else f'M{x2+8} {y2-7} l-8 7 8 7'
    return path(f'M{x1} {y1} H{x2} '+tip,color)

def circle(x,y,r,fill=PAPER,stroke=LINE):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'

def person(x,y,scale=1,color=INK):
    return f'<g transform="translate({x} {y}) scale({scale})">'+circle(0,-14,12,PAPER,color)+path('M-24 28 v-6 c0 -27 48 -27 48 0 v6',color,2.5)+'</g>'

def icon(x,y,kind,color=INK,scale=1):
    icons={
      'screen':'M0 0 H56 V36 H0 Z M28 36 V47 M13 48 H43',
      'doc':'M3 0 H33 L46 13 V55 H3 Z M33 0 V13 H46 M12 25 H35 M12 35 H35 M12 45 H28',
      'chat':'M0 0 H54 V33 H23 L10 44 V33 H0 Z M12 11 H42 M12 22 H31',
      'check':'M0 20 L13 33 L40 0',
      'book':'M0 3 Q14 -3 27 3 Q40 -3 54 3 V44 Q40 38 27 44 Q14 38 0 44 Z M27 3 V44',
      'search':'M35 17 a17 17 0 1 1 -34 0 a17 17 0 1 1 34 0 M30 30 L49 49',
      'calendar':'M0 7 H50 V48 H0 Z M0 19 H50 M13 0 V12 M37 0 V12 M10 29 H19 M28 29 H39 M10 39 H19',
      'branch':'M0 8 H20 V39 H49 M20 8 H49 M20 24 H49',
    }
    return f'<g transform="translate({x} {y}) scale({scale})">'+path(icons[kind],color,2.3)+'</g>'

def svg(label, body, height=330):
    return f'<svg class="ws-visual" viewBox="0 0 1112 {height}" role="img" aria-label="{escape(label)}">{body}</svg>'

def meeting():
    a=rect(6,45,316,194,PAPER,12,LINE)+rect(22,61,284,146,PANEL,5)
    a+=icon(129,86,'screen',scale=1.1)+text(164,180,'画面を見せる',26,weight=700,anchor='middle')
    a+=path('M164 239 V263 M116 264 H212',INK)+text(164,308,'TeamsのWeb会議',18,DIM,anchor='middle')
    a+=arrow(342,140,393,140)
    a+=rect(414,44,275,90)+text(437,80,['ここまでできた','ここで困っている'],22)
    a+=path('M437 134 l0 12 17 -12',LINE)+rect(452,164,250,74,PAPER,12,LINE)
    a+=text(477,196,['気になる点や','使ってみたい場面を話す'],19)
    a+=arrow(724,140,779,140)
    a+=circle(954,134,100,ACCENT,ACCENT)+icon(932,83,'check',PAPER,1.1)
    a+=text(954,160,['次に試すことを','決める'],25,PAPER,700,'middle',36)
    a+=text(954,278,'完成前でも共有する',19,DIM,anchor='middle')
    return svg('Teamsで画面を見せ、困りごとを話し、次に試すことを決める',a)

def support():
    a=person(95,147,1.6)+text(95,236,'参加者',25,weight=700,anchor='middle')
    a+=person(1013,147,1.6)+text(1013,236,'主催者',25,weight=700,anchor='middle')
    a+=rect(336,12,442,107,PAPER,12,LINE)+icon(362,39,'book',scale=.8)
    a+=text(426,53,'ブログ・動画',25,weight=700)+text(426,86,'必要なときに、自分で学ぶ',19,DIM)
    a+=path('M969 120 V65 H801')+arrow(315,65,137,65)+path('M137 65 V110')
    a+=rect(336,182,442,112,ACCENT)+icon(365,216,'chat',PAPER,.8)
    a+=text(428,223,'Teamsで相談する',25,PAPER,700)+text(428,259,'投稿 ＋ 月1回のよろず相談会（案）',17,PAPER)
    a+=path('M137 187 V236 H315')+arrow(801,236,969,236)+path('M969 236 V191')
    return svg('主催者のブログや動画から学び、Teamsで主催者に相談する',a)

def handoff():
    a=person(105,134,1.5)+text(105,220,'作った人',23,weight=700,anchor='middle')
    a+=arrow(169,137,359,137)
    a+=rect(385,20,349,251,PAPER,12,LINE)+icon(409,43,'doc',scale=.7)
    a+=text(465,71,'説明と仕組み',24,weight=700)
    for y,t in [(123,'何に使えるか'),(175,'どう使うか'),(227,'何が必要か')]:
        a+=circle(421,y-7,5,INK,INK)+text(445,y,t,22)
    a+=arrow(756,137,919,137)
    a+=circle(1002,127,66,ACCENT,ACCENT)+person(1002,123,1.25,PAPER)
    a+=text(1002,227,'初めて使う人',23,weight=700,anchor='middle')
    a+=text(557,316,'作者に聞かなくても、目的を達成できる',25,ACCENT,700,'middle')
    return svg('作った人が説明と仕組みを渡し、初めて使う人が作者への質問なしで目的を達成する',a)

def evaluation():
    a=rect(0,8,540,278,PAPER,12,LINE)+text(28,47,'同じ人の回答を比べる',25,weight=700)
    for i,t in enumerate(['事前','中間','終了']):
        x=98+i*165
        if i<2:a+=path(f'M{x+30} 97 H{x+135}')
        a+=circle(x,97,24,PANEL,LINE)+text(x,104,str(i+1),20,anchor='middle')
        a+=text(x,147,t,21,anchor='middle')
    a+=text(28,192,['実務で使った日数 ／ できることを5段階で回答'],17,DIM)
    a+=text(28,239,'向上・同じ・低下の人数',26,ACCENT,700)
    a+=text(28,267,'項目ごとに集計する',17,DIM)
    a+=rect(574,8,538,278,PAPER,12,LINE)+text(602,47,'実際にできたことを確かめる',25,weight=700)
    a+=icon(620,84,'doc',scale=.9)+arrow(696,112,741,112)+icon(782,86,'check',scale=1.05)
    a+=text(874,105,['成果物','他者の試用記録'],20)
    a+=text(602,192,'新しくできたことの実例',21,weight=700)
    a+=text(602,238,['作者の補足なしで使えた数と、','まだ難しかったことを報告する'],20,DIM)
    return svg('3時点のアンケートの人数比較と、成果物や他者の試用記録による確認を組み合わせる',a,310)

CORE_QUESTIONS=[
 'AIを使えそうな仕事を思いつけますか。',
 '仕事で困っている理由を整理できますか。',
 'AIに、してほしいことを伝えられますか。',
 'AIに、いくつかの作業をまとめて頼めますか。',
 '作ったものの使い方を、他の人にも分かるように説明できますか。',
 'AIの答えが間違っていないか確かめられますか。',
 '他の人からの感想をもとに、作ったものを直せますか。',
]
CORE_SCALE=['まだやり方が分からない','やり方は分かるが、まだできない','手助けがあればできる','一人でできる','状況に合わせてやり方を変えられる']
PM_TASKS=['資料に使う情報を集める','会議で決まったことをまとめる','関係者の意見の違いを整理する','仕事の遅れや困りごとを見つける','メンバーに聞くことを考える','仕事の手順を他の人に伝える']
B_SCALE=['使い方が分からない','使えそうだが、まだ試していない','試したが、仕事では使っていない','仕事で使った','仕事で繰り返し使っている']

def scale(x,y,values,width=448):
    a=text(x,y,'今の自分に近いものを選ぶ',21,weight=700)
    for i,t in enumerate(values):
        yy=y+20+i*44
        a+=rect(x,yy,width,39,PANEL,6)+circle(x+22,yy+19,11,PAPER,LINE)
        a+=text(x+22,yy+25,str(i),15,DIM,anchor='middle')+text(x+46,yy+26,t,18)
    return a

def questionnaire():
    a=text(0,25,'質問の例',19,DIM)
    qs=[['AIを使えそうな仕事を','思いつけますか。'],['AIに、してほしいことを','伝えられますか。'],['AIの答えが間違っていないか','確かめられますか。']]
    for i,q in enumerate(qs):
        y=42+i*92
        a+=rect(0,y,574,80,PAPER,10,LINE)+text(24,y+32,q,23,gap=32)
    a+=scale(631,25,CORE_SCALE,481)
    a+=text(631,309,'「試す機会がない」も選べる',18,DIM)
    return svg('身近な言葉の3つの質問に、今の自分に近い5段階の答えを選ぶ',a)

def pm_survey():
    a=text(0,25,'普段の仕事',19,DIM)
    labels=[['資料に使う','情報を集める'],['会議で決まった','ことをまとめる'],['関係者の意見の','違いを整理する'],['仕事の遅れや','困りごとを見つける'],['メンバーに','聞くことを考える'],['仕事の手順を','他の人に伝える']]
    icons=['search','doc','branch','calendar','chat','book']
    for i,(lines,kind) in enumerate(zip(labels,icons)):
        x=(i%2)*292;y=42+(i//2)*90
        a+=rect(x,y,278,78,PAPER,9,LINE)+icon(x+15,y+19,kind,scale=.55)
        a+=text(x+56,y+31,lines,18,gap=28)
    a+=scale(631,25,B_SCALE,481)
    a+=text(631,309,'担当していない仕事は「対象外」',18,DIM)
    return svg('PMとPLの6つの仕事について、AIを使った経験を5段階で答える',a)

def agents():
    a=person(95,98,1.5)+text(95,185,'人',23,weight=700,anchor='middle')+text(95,222,['してほしいことを','伝える'],18,DIM,anchor='middle')
    a+=arrow(169,113,311,113)
    a+=rect(335,9,448,278,PAPER,14,LINE)+text(559,52,'エージェント',27,weight=700,anchor='middle')
    a+=text(559,94,'道具を使って仕事を進める',20,DIM,anchor='middle')
    a+=icon(413,124,'search',scale=.6)+icon(533,124,'doc',scale=.6)+icon(653,124,'screen',scale=.6)
    a+=rect(358,192,402,73,ACCENT,10)+text(379,224,'Skills',20,PAPER,700)+text(379,249,'必要なときに読む手順・判断の目安',17,PAPER)
    a+=arrow(808,113,925,113)+icon(972,69,'doc',scale=1.25)
    a+=text(1004,187,'結果',23,weight=700,anchor='middle')+text(1004,222,['人が確かめ、','次の指示を出す'],18,DIM,anchor='middle')
    return svg('人が依頼し、Skillsを参照するエージェントが道具を使い、結果を人が確認する',a,310)

def learning():
    a=rect(0,12,526,277,PAPER,12,LINE)+text(30,54,'考え方を学ぶ',27,weight=700)
    a+=rect(30,82,181,137,PANEL,8)+path('M101 116 l0 65 53 -32 Z',ACCENT,1,ACCENT)
    a+=text(245,117,['何を任せるか','何を伝えるか','どう確かめるか'],23,gap=43)
    a+=text(30,264,'短い動画で、繰り返し学ぶ',19,DIM)
    a+=rect(572,12,540,277,PAPER,12,LINE)+text(602,54,'操作を試す',27,weight=700)
    for i,t in enumerate(['作る','動かす','確かめる']):
        x=659+i*176
        a+=circle(x,139,44,PANEL,LINE)+text(x,147,t,20,weight=700,anchor='middle')
        if i<2:a+=arrow(x+55,139,x+122,139)
    a+=text(602,228,['最小限の操作から始め、','自分の課題へつなげる。'],20,DIM)
    return svg('概念動画で考え方を学び、作る・動かす・確かめる操作を試す',a,310)
