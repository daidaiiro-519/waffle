"""図表10種の入力。Mermaidに渡したのと同じ内容を、こちらの語彙で書いたもの。"""
DATA = {
 "sequence": {"kind":"exchange","participants":["Orchestrator","Waffle","advisor"],"steps":[
   {"kind":"call","from":"Orchestrator","to":"Waffle","text":"骨格を作る"},
   {"kind":"return","from":"Waffle","to":"Orchestrator","text":"埋める場所の一覧"},
   {"kind":"frame","label":"loop","span":2},
   {"kind":"call","from":"Orchestrator","to":"advisor","text":"敵対的に確かめる"},
   {"kind":"return","from":"advisor","to":"Orchestrator","text":"反証、または支持"},
   {"kind":"note","text":"反証が出たら、差し戻して調べ直す"}]},
 "gantt": {"kind":"lanes","span":12,"axis":["8/01","8/04","8/07","8/10","8/12"],"rows":[
   {"name":"調べる","bars":[{"from":0,"to":3,"label":"3日"}]},
   {"name":"決める","bars":[{"from":3,"to":5,"label":"2日"}]},
   {"name":"引き継ぐ","bars":[{"from":5,"to":6,"tone":"warn","label":"1日"}]},
   {"name":"作る","bars":[{"from":6,"to":11,"label":"5日"}]}]},
 "timeline": {"kind":"lanes","span":9,"axis":["過去","","現在"],"rows":[
   {"name":"v8","bars":[{"from":0,"to":3,"label":"操作保証を持つ"}]},
   {"name":"v9","bars":[{"from":3,"to":6,"tone":"soft","label":"鍵の一意性"}]},
   {"name":"v10","bars":[{"from":6,"to":9,"label":"2ブロックを落とす"}]}]},
 "journey": {"kind":"lanes","span":5,"axis":["1","3","5"],"rows":[
   {"name":"既存を読む","bars":[{"from":0,"to":3,"tone":"soft","label":"3"}]},
   {"name":"advisorに聞く","bars":[{"from":0,"to":4,"label":"4"}]},
   {"name":"骨格を作る","bars":[{"from":0,"to":5,"label":"5"}]},
   {"name":"値を埋める","bars":[{"from":0,"to":3,"tone":"warn","label":"3"}]}]},
 "gitGraph": {"kind":"lanes","span":8,"rows":[
   {"name":"main","bars":[{"from":0,"to":2,"label":"骨格"},{"from":6,"to":8,"label":"合流"}]},
   {"name":"spec","bars":[{"from":2,"to":6,"tone":"soft","label":"基準を足す"}]}]},
 "pie": {"kind":"share","centre":"15部品","slices":[
   {"name":"文章の部品","value":10},{"name":"図の部品","value":5}]},
 "xychart": {"kind":"bars","slices":[
   {"name":"v8","value":56},{"name":"v9","value":10},{"name":"v10","value":4}]},
 "sankey": {"kind":"flow","links":[
   {"from":"構造化データ","to":"Markdown","value":15},
   {"from":"構造化データ","to":"HTML","value":4}]},
 "quadrant": {"kind":"matrix","x":"差別化が小さい ← → 大きい","y":"複雑さ 低 ← → 高",
   "quadrants":["中核","見直す","一般","補完"],"points":[
   {"name":"文書の検証","x":.78,"y":.74},{"name":"描画","x":.38,"y":.55},
   {"name":"設定の読み込み","x":.18,"y":.18}]},
 "block": {"kind":"blocks","cols":3,"cells":[
   {"name":"受け口"},{"name":"応用","tone":"focus"},{"name":"領域"},
   {"name":"CLI / MCP"},{"name":"ユースケース","tone":"focus"},{"name":"モデル"}]},
}