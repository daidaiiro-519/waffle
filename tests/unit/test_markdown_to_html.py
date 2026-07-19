"""markdown_to_html の単体テスト（Waffle自身が生成するMDの限定語彙のみを対象とする）。"""
from waffle.domain.services.markdown_to_html import convert


def test_見出しレベルごとにhタグへ変換する():
    html = convert("# H1\n\n## H2\n\n### H3")
    assert "<h1>H1</h1>" in html
    assert "<h2>H2</h2>" in html
    assert "<h3>H3</h3>" in html


def test_段落はpタグになる():
    html = convert("これは段落です。")
    assert "<p>これは段落です。</p>" in html


def test_水平線はhrタグになる():
    html = convert("段落1\n\n---\n\n段落2")
    assert "<hr" in html


def test_箇条書きはulタグになる():
    html = convert("- 項目1\n- 項目2")
    assert "<ul>" in html
    assert "<li>項目1</li>" in html
    assert "<li>項目2</li>" in html


def test_番号付き箇条書きはolタグになる():
    html = convert("1. 項目1\n2. 項目2")
    assert "<ol>" in html
    assert "<li>項目1</li>" in html


def test_テーブルはtableタグになる():
    md = "| コード | 条件 |\n|---|---|\n| `X` | 何か起きる |"
    html = convert(md)
    assert "<table>" in html
    assert "<th>コード</th>" in html
    assert "<td><code>X</code></td>" in html
    assert "<td>何か起きる</td>" in html


def test_テーブルはスクロール可能なコンテナで包まれる():
    md = "| a | b |\n|---|---|\n| 1 | 2 |"
    html = convert(md)
    assert '<div class="table-scroll"><table>' in html
    assert "</table></div>" in html


def test_テーブルセル内のbrタグはそのまま透過する():
    md = "| 分類 | 詳細 |\n|---|---|\n| A | <br>- item1<br>- item2 |"
    html = convert(md)
    assert "<br>- item1<br>- item2" in html


def test_インライン強調とインラインコードを変換する():
    html = convert("これは**重要**で`code`です。")
    assert "<strong>重要</strong>" in html
    assert "<code>code</code>" in html


def test_mermaidコードフェンスはpre_mermaidになる():
    md = "```mermaid\nsequenceDiagram\n  A->>B: hi\n```"
    html = convert(md)
    assert '<pre class="mermaid">' in html
    assert "sequenceDiagram" in html
    assert "A-&gt;&gt;B: hi" in html or "A->>B: hi" in html


def test_mermaid以外のコードフェンスはpre_codeになる():
    md = "```python\nprint(1)\n```"
    html = convert(md)
    assert "<pre><code" in html
    assert "print(1)" in html


def test_コードフェンス内はインライン変換されない():
    md = "```\n**not bold**\n```"
    html = convert(md)
    assert "**not bold**" in html
    assert "<strong>" not in html
