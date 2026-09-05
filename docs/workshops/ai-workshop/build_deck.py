"""Build the workshop proposal from the local slide-deck HTML template."""
from pathlib import Path
import html
import json
import re

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
TEMPLATE = ROOT / '.claude/skills/slide-deck/references/deck-template.html'

def esc(s):
    return html.escape(s)

def diagram(nodes, *, caption='', hot=-1):
    count = len(nodes)
    width = 500 if count == 2 else 1040
    gap = 44
    box = (width - gap * (count - 1)) / count
    pieces = [f'<svg class="ws-flow" viewBox="0 0 {width} 172" role="img" aria-label="{esc(caption or "、次に".join(n[0] for n in nodes))}">']
    for i, (title, sub) in enumerate(nodes):
        x = i * (box + gap)
        fill = '#b64326' if i == hot else '#e9e5da'
        ink = '#fffaf2' if i == hot else '#252b29'
        dim = '#fff1e9' if i == hot else '#59605a'
        pieces.append(f'<rect x="{x}" y="18" width="{box}" height="126" rx="8" fill="{fill}"/>')
        pieces.append(f'<text x="{x+box/2}" y="69" text-anchor="middle" fill="{ink}" font-size="25" font-weight="700">{esc(title)}</text>')
        pieces.append(f'<text x="{x+box/2}" y="106" text-anchor="middle" fill="{dim}" font-size="17">{esc(sub)}</text>')
        if i < count - 1:
            end = x + box
            pieces.append(f'<path d="M {end+10} 81 H {end+32} m -7 -7 l 7 7 -7 7" stroke="#80867e" stroke-width="2" fill="none"/>')
    pieces.append('</svg>')
    return ''.join(pieces)

def table(headers, rows, cls=''):
    return '<table class="ws-table '+cls+'"><thead><tr>'+''.join('<th>'+x+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+c+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table>'

def note(s):
    return f'<p class="ws-note">{s}</p>'

def group_svg():
    parts=['<svg class="ws-groups" viewBox="0 0 570 285" role="img" aria-label="15人を、3人ずつ5組の相談グループにする提案">']
    for g, (x,y) in enumerate([(98,72),(283,72),(468,72),(190,217),(375,217)]):
        pts=[(x-32,y+19),(x+32,y+19),(x,y-32)]
        parts.append(f'<path d="M{pts[0][0]} {pts[0][1]} L{pts[1][0]} {pts[1][1]} L{pts[2][0]} {pts[2][1]} Z" fill="none" stroke="#b5b8ab" stroke-width="2"/>')
        for k,(px,py) in enumerate(pts):
            parts.append(f'<circle cx="{px}" cy="{py}" r="15" fill="{"#b64326" if g==2 and k==2 else "#f4f1e8"}" stroke="{"#b64326" if g==2 and k==2 else "#4f5952"}" stroke-width="2"/>')
    parts.append('</svg>')
    return ''.join(parts)

# The slide order and one-sentence claims are fixed before layout construction.
SLIDES = [
 dict(label='企画の目的', title='身近な課題から、<br>新しい仕組みを生み出す力を育てる。', cls='ws-cover',
      intro='社内AI人材育成ワークショップ｜下期実施案',
      body=diagram([('課題を選ぶ','自分の仕事を観察する'),('小さく作る','AIと仕組みを形にする'),('試して直す','他者の反応から学ぶ')],hot=2)+note('主催者の条件：約15名の開発者・PM・PL　／　10月開始・集合日の固定は困難'),
      notes='この企画は、顧客提案を直接練習するものではありません。その土台となる、自分で課題を見つけて形にする力を育てます。身近な業務を対象に、エージェントやSkillsで小さな仕組みを作り、実際に試して改善します。対象は約15名、10月開始という主催者の条件に基づきます。'),
 dict(label='育てたい力', title='課題を選び、試して直す力を共通の土台にする。',
      intro='開発者もPM・PLも、自分の判断を成果物で確かめる。',
      body=table(['育てたい力','参加者の行動','学びが見える記録'],[
          ['課題を捉える','困る場面と、変えたい状態を決める','課題の説明と対象者'],
          ['AIに仕事を任せる','目的・材料・制約・完了条件を渡す','エージェントやSkillの設定'],
          ['<b>試して改善する</b>','他者の使用結果から、判断を見直す','試した結果と修正理由']]),
      notes='0から1を作る力を、観察できる行動に置き換えます。高度なアプリを作ったかどうかだけでは評価しません。本人が対象者と課題を説明でき、AIに必要な情報を渡し、実際の結果を踏まえて判断を修正できたかを見ます。これが、将来の顧客との課題探索にもつながる育成上の狙いです。'),
 dict(label='テーマの設計', title='幅のあるテーマから、取り組む課題を本人が決める。',
      intro='主催者は困りごとの領域を示し、解決方法と成果物の形は参加者が選ぶ。',
      body=table(['開発者向けの領域','PM・PL向けの領域'],[
          ['開発プロセスの手間を減らす','提案準備や関係者調整の手間を減らす'],
          ['Webアプリを作り始めやすくする','メンバーの状況を把握しやすくする'],
          ['新しい参加者が仕事を始めやすくする','相談や知識共有が生まれやすくする']])+note('テーマを絞る問い：誰が、どんな場面で困るか。何が変われば役に立ったと言えるか。'),
      notes='職種ごとに完成品を指定するのではなく、取り組む領域を選べるようにします。たとえばPM・PLなら、資料を作ることだけでなく、判断材料を集める、認識のずれを見つける、相談の入口を作るといった仕事も対象です。これは用途のヒントであり、推奨する解法の一覧ではありません。参加者自身が経験した場面へ絞り込みます。'),
 dict(label='エージェントとSkills', title='エージェントに役割を与え、Skillsで仕事の進め方を渡す。',
      intro='人が目的と制約を決め、AIが道具を使って実行し、人が結果を確かめる。',
      body=diagram([('人','目的・制約・完了条件'),('エージェント','役割・材料・使える道具'),('実行結果','人が確認し、次を決める')],hot=1)+
           '<div class="ws-skill-link"><span class="ws-pill">Skills</span><span>必要なときに参照する手順・判断基準・参考資料をまとめる。</span></div>'+note('Kiroの機能の説明：公式ドキュメント「Custom agents」「Agent Skills」。利用環境は開始前に確認する。'),
      notes='この図は学習のために仕事の関係を整理したものです。カスタムエージェントには役割や使える道具、参照する情報などを設定できます。Skillsは必要な場面で参照する手順や参考資料のまとまりです。すべてを自律実行させる必要はなく、何を任せて何を人が確認するかを決めることを重視します。Kiro公式資料は付録に記載しています。'),
 dict(label='概念教育', title='教材で考える道具を渡し、操作の入口を支える。',
      intro='音声付きの短いスライド動画を、必要なときに見返せる教材にする。',
      body='<div class="ws-split"><div><p class="ws-eyebrow">概念を学ぶ</p>'+table(['学ぶ内容','考えること'],[
          ['エージェント','任せる仕事と人の判断の境界'],['情報と道具','目的に必要な材料の選び方'],['Skillsと検証','手順の共有と結果の確かめ方']])+'</div><div>'+diagram([('触る','作成・実行'),('確かめる','読込・結果')],hot=1)+'<p class="ws-copy">操作教材は最小構成。<br>完成した業務事例の再現を課題にしない。</p></div></div>',
      notes='主教材は概念中心の動画にし、操作の説明は独立した短い補助教材にします。形式を知らないために始められない状態は防ぎます。一方、業務課題の完成例を見せすぎると解法を固定するため、主教材には目的や分担の図を置き、用途のヒントは別途少量だけ公開します。教材はこれから制作する計画で、この提案デッキが受講者向け動画ではありません。'),
 dict(label='下期の進め方', title='半年間で、試作から他者の利用へ進める。',
      intro='2026年10月〜2027年3月の実施案。月ごとの区切りで、非同期に進める。',
      body='<div class="ws-phases"><svg class="ws-phase-path" viewBox="0 0 1112 240" role="img" aria-label="10・11月の試作から、12・1月の見直しを経て、2・3月の他者利用へ進む"><path d="M 355 107 h 21 m -6 -6 l 6 6 -6 6 M 736 107 h 21 m -6 -6 l 6 6 -6 6" fill="none" stroke="#747c6e" stroke-width="2"/></svg><div><p class="ws-date">10・11月</p><h3>学び、試作する</h3><p>概念教材を視聴する<br>課題を選び、小さく動かす</p></div><div class="ws-phase-hot"><p class="ws-date">12・1月</p><h3>見せて、絞り直す</h3><p>12月に中間成果を共有する<br>他者の反応で方向を見直す</p></div><div><p class="ws-date">2・3月</p><h3>使ってもらい、残す</h3><p>別の人が試して改善する<br>3月に成果と学びを共有する</p></div></div>'+note('日程は提案。主催者指定の「10月開始・下期」を、上記の期間として計画している。'),
      notes='毎週同じ時間に集まることは前提にしません。10月から翌3月までを提案期間とし、12月に中間共有、3月に最終共有を置きます。初期から試作に触れ、中間発表まで完成を待たないようにします。途中のテーマ変更も、試した結果に理由があれば認めます。休暇や繁忙期を踏まえ、実働20週を工数試算の仮定にしています。'),
 dict(label='参加形態', title='個人の試行を、少人数の相談グループで支える。',
      intro='一人ひとりが作り、互いの成果物を試す。得意な人への作業集中を避ける。',
      body='<div class="ws-split"><div>'+group_svg()+'<p class="ws-source">構成案：15名を3人ずつ、5組の相談グループにする。<br>共同制作も可。全員が操作と自分の判断を説明する。</p></div><div class="ws-plain-stack"><div><h3>個人が持つもの</h3><p>選んだ課題、動かした仕組み、<br>自分で判断したことの記録。</p></div><div><h3>相談グループで行うこと</h3><p>詰まりの相談、別の視点からの質問、<br>成果物の相互利用。</p></div></div></div>',
      notes='約15名という条件から、3名ずつ5組の相談グループを提案します。グループに一つの完成品を課す方式ではなく、個人が自分の課題と試行を持ちます。共同制作を選ぶ場合も、各人が設定を動かしたことと自分の判断を説明できることを条件にします。グループ構成は職種よりも、利用者として異なる視点を返せる組み合わせを優先します。'),
 dict(label='成果物の条件', title='成果物は、別の人が使える仕組みにする。',
      intro='アプリ、分析、文書生成など、出力の形式は自由に選べる。',
      body=diagram([('仕組みを渡す','設定・Skillなどと必要な材料'),('別の人が試す','説明に沿って実行する'),('結果を残す','使えた点・修正した理由')],hot=2)+note('最低限の提出物：動く仕組み／使い方／試した記録。<br>エージェントやSkillsは既存の利用・改良も可。選んだ構成の役割を説明する。'),
      notes='一度きりの生成結果に加え、再び使うために必要なものを渡せる状態を目指します。エージェント設定やSkill、入力例、実行の説明、試行記録を残します。エージェントやSkillsは既存の利用・改良も認め、選んだ構成の役割を説明します。両方の新規作成を必須条件にはしません。誰かが実際に使い、困った点を改善する経験を成果物の条件にします。既存の構成を改良する場合も、自分が変えた理由を説明します。'),
 dict(label='中間成果物発表', title='中間発表で、次に試すことを見つける。', cls='ws-sharing',
      intro='12月は、途中の成果と判断に迷っている点を共有する。',
      body='<div class="ws-split"><div><p class="ws-eyebrow">発表の形式・提案</p><div class="ws-hours"><span>5</span><small>分の録画／人</small></div><p class="ws-copy">課題・動作・困っている点を見せる。</p><p class="ws-source">録画＋要点メモを共有する。録画が難しい場合は、<br>動作画面と説明文でも提出できる。</p></div><div>'+table(['進め方','参加者が行うこと'],[['共有する','1週間で提出・視聴・コメント'],['相互に返す','役立つ場面、疑問、試したい点'],['次を決める','続ける・絞る・方向を変える']])+'</div></div>',
      notes='中間発表は非同期の録画または動作画面と説明文で成立させます。参加者は同じ相談グループの2人分を必ず見て、他グループの1人分も選んで確認する案です。発表者に点数を付けるより、次に何を試すとよいかを返します。最終共有も同じ形式にし、最初と最後で何を判断し直したかを追加してもらいます。'),
 dict(label='サポート体制', title='Teamsとブログで、試行を止めずに支える。',
      intro='相談を個別に受け止め、繰り返す疑問は共有できる教材に変える。',
      body=diagram([('Teamsで相談','目的・試行・詰まりを共有'),('主催者が支援','整理・ヒント・操作補助'),('ブログで共有','学びを再利用できる形にする')],hot=1)+note('運営案：隔週で短い進捗投稿。主催者は週2回を目安に確認し、相談が止まった人にも声をかける。'),
      notes='主催者は正解を代わりに作るのではなく、問題の整理や次の試行を支えます。操作の障害は直接支援し、課題選択の相談には問い返しや比較の観点を返します。ブログは必読記事を増やし続けず、概念教材と補助記事の索引を設けます。週2回の確認は運営案であり、応答期限として確約する場合は担当者の業務時間を先に確保します。'),
 dict(label='成果の確認', title='成果と判断の変化を、同じ観点で確かめる。', cls='ws-eval',
      intro='開始時・中間・終了時の記録を比較し、本人と主催者が確認する。',
      body=table(['観点','確かめること','証拠'],[
          ['課題の設定','誰の何を変えるか、本人が説明できる','課題メモと選んだ理由'],
          ['AIへの委任','必要な材料を渡し、出力を確認できる','設定と実行記録'],
          ['検証と改善','他者の反応で仕組みを修正できる','使用結果と変更内容'],
          ['共有と再利用','別の人が使い始められる','使い方と他者の試行記録']])+note('事業効果は試行で測る。削減時間は、確認・修正・保守の手間も含めて扱う。'),
      notes='本人の満足度と完成品の見栄えだけでは、育成の成果を確かめられません。同じ4観点を開始時、中間、終了時に使います。開始時は現状の説明と最小操作を記録し、未経験の観点は未実施とします。運営側は継続率、他者が使えた成果物数、相談の停滞も見ますが、目標値は事前状況を確認して決めます。業務効果の数値は、実測してから報告します。'),
 dict(label='部長への依頼', title='育成方針への合意と、学習時間の確保をお願いする。',
      intro='今回相談すること：自分で課題を選んで試す育成方針と、業務内の学習時間。',
      body='<div class="ws-split"><div><p class="ws-eyebrow">参加者の時間・提案</p><div class="ws-hours"><span>週2</span><small>時間／人</small></div><p class="ws-copy">教材・試作・共有を業務時間に含める。</p><p class="ws-source">試算：2時間 × 実働20週 × 15名＝延べ600時間。<br>20週は仮定。運営工数と利用料金は別途確認する。</p></div><div>'+table(['実施前に詰める条件','具体的な確認事項'],[
          ['運営担当','教材制作と相談対応の工数'],['利用環境','Kiroの利用枠・料金・データの扱い'],['実施日程','中間・最終共有の期間と上長調整']])+'</div></div>',
      notes='今回は、本人が課題を選んで試す育成方針への合意と、参加者の学習時間の確保を相談します。参加者の週2時間は提案です。実働20週で一人40時間、15名で延べ600時間という試算です。実施に必要な運営担当、利用環境、日程はこの後に具体化します。運営工数と利用料金は600時間に含みません。運営工数の暫定試算は運営設計書にあり、必要な予算の承認を受ける前に担当者と利用契約を確認します。削減効果の金額はまだ見積もっていません。'),
 dict(label='付録｜PM・PLのテーマ', title='PM・PL向けには、判断・調整・相談の負荷を題材にする。',
      intro='用途のヒント。参加者は、実際に経験した場面から自分の課題を選ぶ。',
      body=table(['テーマの領域','困りごとの例','参加者が確かめること'],[
          ['判断の準備','提案のたびに、必要な材料を探し直す','何が揃えば判断を始められるか'],
          ['関係者の調整','決まったことと保留事項が混ざってしまう','どこで認識がずれているか'],
          ['チームの相談','困りごとが、問題になってから分かる','どの場面なら相談しやすいか']])+note('メンバー個人を自動採点する題材より、仕事の状況と支援の必要性を共有する題材を勧める。'),
      notes='PM・PLの仕事を、文書作成だけに狭めないための補足です。進捗把握には情報収集、解釈、支援判断が含まれます。コミュニケーション活性化も、発言数を増やすことに固定せず、必要な相手に相談しやすくなったかを確かめます。これらは主催者向けの題材候補で、受講者には課題選択後に必要なヒントだけを渡します。'),
 dict(label='付録｜利用環境', title='Kiroを共通の実行環境にし、Claudeは補助に使う。',
      intro='Claudeを使えない参加者も、必須課題を完了できる構成にする。',
      body=table(['主環境：Kiro','補助環境：Claude'],[
          ['エージェントの設定・実行','利用可能な範囲での壁打ち'],['Skillsの作成・利用','文章や説明の別視点での確認'],['成果物の試行と改善','任意の補助作業']])+ '<p class="ws-source">開始前に確認：社内のIDE／CLIの版、利用枠、ファイル・コマンドの権限。<br>機能の根拠：<a href="https://kiro.dev/docs/skills/">Kiro Agent Skills</a> ／ <a href="https://kiro.dev/docs/cli/custom-agents/creating/">Creating custom agents</a>（2026-09-05確認）。<br>本デッキ作成時点で、社内Kiro環境での動作検証は未実施。</p>',
      notes='Kiro公式ドキュメントではAgent Skillsとカスタムエージェントの作成方法が説明されています。ただし社内で導入済みの版と設定は未確認です。初回教材を収録する前に参加者と同じ環境で、作成、読み込み、実行、結果確認までを試します。教材は概念編と操作編に分け、機能更新時は操作編だけを差し替えられるようにします。')
]

CSS = '''
:root{--ground:#f4f1e8;--surface:#e9e5da;--surface-2:#e1dfd3;--paper:#fffaf2;--ink:#252b29;--dim:#59605a;--faint:#686f65;--line:#d5d6c9;--accent:#b64326;--accent-dim:#873f2b;--serif:'Noto Sans JP','Yu Gothic',sans-serif;--sans:'Noto Sans JP','Hiragino Sans','Yu Gothic',sans-serif;--mono:var(--sans)}
body{font-feature-settings:normal;background:#deded3}
.stage{background:var(--ground)}
.slide{padding:84px 84px 78px}
.kicker{font-family:var(--sans);font-size:14px;letter-spacing:.06em;color:var(--dim);margin-bottom:20px;gap:12px}
.kicker::after{display:none}
.ws-mark{display:inline-block;width:12px;height:12px;border:2px solid #6d766a;border-radius:50%;position:relative}
.ws-mark::after{content:'';position:absolute;left:16px;top:3px;width:13px;height:2px;background:#b7bcae}
.ws-kicker-label{padding-left:17px}
h1,h2{font-family:var(--sans);font-weight:700;text-wrap:initial;letter-spacing:-.03em}
h1{font-size:51px;line-height:1.43} h2{font-size:36px;line-height:1.46;margin-bottom:16px}
.ws-intro{font-size:20px;line-height:1.7;max-width:none;color:var(--dim)}
.body{justify-content:flex-start;padding-top:35px;gap:16px;min-height:0}
.ws-cover .body{padding-top:29px}
.ws-cover .ws-intro{font-size:19px;margin-top:14px}
.ws-flow{width:100%;height:auto;max-height:184px;display:block;flex:none;font-family:var(--sans)}
.ws-note{font-size:16px;line-height:1.8;max-width:none;color:var(--dim);margin-top:8px}
.ws-table{font-family:var(--sans);width:100%;font-size:20px;border-collapse:collapse;table-layout:fixed}
.ws-table th{font-family:var(--sans);font-size:15px;color:var(--dim);font-weight:500;letter-spacing:0;text-transform:none;padding:0 16px 15px;border-bottom:1px solid #b8bdb0;line-height:1.5}
.ws-table td{padding:19px 16px;color:var(--ink);border-bottom:1px solid var(--line);font-size:19px;line-height:1.65}
.ws-table td:first-child{font-weight:500}.ws-table b{color:var(--accent)}
.ws-split{display:grid;grid-template-columns:1.06fr 1fr;gap:54px;align-items:start}
.ws-split .ws-flow{height:165px;max-height:none;margin-top:24px}
.ws-split .ws-table td{font-size:18px;padding:16px 10px}.ws-split .ws-table th{padding-left:10px;padding-right:10px}
.ws-skill-link{display:flex;justify-content:center;align-items:center;gap:20px;font-size:20px;padding:8px 0}
.ws-pill{display:inline-block;padding:10px 24px;border:1px solid #939d8b;border-radius:30px;font-size:17px;color:var(--dim)}
.ws-eyebrow{font-size:16px;margin-bottom:18px;color:var(--dim)}
.ws-copy{font-size:22px;line-height:1.8;max-width:none;color:var(--ink);margin-top:14px}
.ws-phases{display:grid;grid-template-columns:repeat(3,1fr);gap:30px;position:relative;padding-top:16px}
.ws-phases>div{position:relative;padding:29px 25px;background:#e9e5da;border-radius:8px}
.ws-phase-path{position:absolute;left:0;top:16px;width:100%;height:240px;pointer-events:none}
.ws-phases>.ws-phase-hot{background:var(--accent);color:#fffaf2}
.ws-date{font-size:18px;color:var(--dim);margin-bottom:21px}
.ws-phases h3{font-size:23px;margin-bottom:16px}.ws-phases p:not(.ws-date){font-size:18px;line-height:1.9;max-width:none}
.ws-phase-hot p{color:#fff2e7}.ws-phase-hot h3{color:#fffaf2}
.ws-groups{width:100%;height:258px;display:block}
.ws-plain-stack{display:flex;flex-direction:column;gap:37px;padding-top:19px}
.ws-plain-stack h3{font-size:25px;margin-bottom:10px}.ws-plain-stack p{font-size:20px;line-height:1.85}
.ws-hours{display:flex;align-items:baseline;gap:18px;padding-top:3px}.ws-hours span{font-size:76px;line-height:1.3;color:var(--accent);font-weight:700;letter-spacing:-.05em}.ws-hours small{font-size:22px}
.ws-source{font-size:14px;line-height:1.8;color:var(--dim);max-width:none;margin-top:16px}
.ws-source a{color:inherit;text-decoration:underline;text-underline-offset:3px;position:relative;z-index:6}
.ws-eval .ws-table td{padding-top:15px;padding-bottom:15px}
.ws-sharing .ws-table th:first-child{width:30%}
.chrome{font-family:var(--sans);font-size:12px;letter-spacing:0;height:48px;padding:0 42px;color:#6c7468}
.hint{opacity:1}.progress{height:2px;background:#adb4a3}
.ws-nav{background:none;border:0;color:inherit;font:inherit;cursor:pointer;pointer-events:auto;padding:7px 15px}
.navzone{width:6%;opacity:0}
@media print{
 @page{size:1280px 720px;margin:0}
 html,body{height:auto;overflow:visible;background:var(--ground)}
 .deck{position:static;overflow:visible}.stage{position:static;width:1280px;height:auto;transform:none!important}
 .slide{position:relative;display:flex!important;height:720px;break-after:page;animation:none!important}
 .chrome,.progress,.navzone{display:none}
}
'''

def build():
    template = TEMPLATE.read_text()
    prefix = template.split('<!-- 01 -->')[0]
    prefix = re.sub(r'<link[^>]+>\s*', '', prefix)
    prefix = prefix.replace('<title>デッキの題名</title>', '<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>身近な課題から、仕組みを生み出す｜社内AI人材育成</title>')
    prefix = prefix.replace('<div class="navzone prev"', '<style>'+CSS+'</style></head><body>\n<div class="navzone prev"', 1)
    slides=[]
    for i, s in enumerate(SLIDES,1):
        heading='h1' if i==1 else 'h2'
        slides.append(f'<section class="slide {s.get("cls", "")}" aria-label="{i}: {esc(re.sub("<[^>]*>", "", s["title"]))}">\n'
            f'<div class="kicker"><span class="ws-mark" aria-hidden="true"></span><span class="ws-kicker-label">{esc(s["label"])}　／　企画案</span></div>\n'
            f'<{heading}>{s["title"]}</{heading}>\n<p class="ws-intro">{esc(s["intro"])}</p>\n<div class="body">{s["body"]}</div>\n</section>')
    suffix=template[template.index('<div class="chrome">'):]
    labels=json.dumps([s['label'] for s in SLIDES],ensure_ascii=False)
    suffix=re.sub(r'const LABELS = .*?;',f'const LABELS = {labels};',suffix)
    suffix=suffix.replace('<span class="hint">← → でめくる</span>','<span class="hint"><button class="ws-nav" id="ws-prev" aria-label="前のスライド">←</button>矢印キーでめくる<button class="ws-nav" id="ws-next" aria-label="次のスライド">→</button></span>')
    suffix=suffix.replace("const prev = ()=> show(i-1);", "const prev = ()=> show(i-1);\n  document.getElementById('ws-prev').addEventListener('click', prev);\n  document.getElementById('ws-next').addEventListener('click', next);\n  addEventListener('hashchange',()=>{const n=parseInt(location.hash.slice(1),10)-1;if(Number.isFinite(n)&&n!==i)show(n);});")
    suffix += '\n</body></html>\n'
    (OUT/'director-deck.html').write_text(prefix+'\n'.join(slides)+suffix)
    notes=['# 部長向け発表原稿\n\n本編12枚、付録2枚。主催者の条件と、今回の運営提案を分けて説明する。\n']
    for i,s in enumerate(SLIDES,1):
        notes.append(f'## {i:02d}　{re.sub("<[^>]*>", "", s["title"])}\n\n{s["notes"]}\n')
    (OUT/'speaker-notes.md').write_text('\n'.join(notes))
    print(f'Built {len(SLIDES)} slides: {OUT / "director-deck.html"}')

if __name__=='__main__':
    build()
