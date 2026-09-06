# -*- coding: utf-8 -*-
"""hl.py — 덱 코드 블록용 최소 구문 강조기.
부 1 덱이 쓰는 클래스(.cm .kw .ty .st .nb .fn .pp)를 그대로 낸다.

TS 덱을 위해 'ts' 를 더했다. 자바스크립트 규칙에 타입 문법 키워드(interface·type·
readonly·satisfies…)와 원시 타입 이름을 얹은 것뿐이다 — 진짜 파서가 아니라
"읽기 좋으라고 칠하는" 물건이라 이 정도로 충분하고, 틀려도 코드 뜻은 안 변한다."""
import re, html

KW = {
 'cpp': """alignas asm auto bool break case catch char class const constexpr continue default delete do
    double else enum explicit extern false float for goto if inline int long namespace new nullptr
    operator private protected public register return short signed sizeof static struct switch template
    this throw true try typedef typename union unsigned using virtual void volatile while""".split(),
 'js': """async await break case catch class const continue default delete do else export extends finally
    for from function get if import in instanceof let new of return set static super switch this throw try
    typeof var void while yield true false null undefined""".split(),
 'make': "ifeq ifneq ifdef ifndef else endif include export define endef PHONY".split(),
 'sh': "cd echo ls make node cat time base64 clang g++ printf stat rm mkdir python3 grep for do done if then fi".split(),
 'json': "true false null".split(),
 'go': """break case chan const continue default defer else fallthrough for func go goto if import
    interface map package range return select struct switch type var true false nil iota""".split(),
 'py': """and as assert async await break class continue def del elif else except finally for from global
    if import in is lambda nonlocal not or pass raise return try while with yield True False None self""".split(),
}
KW['ts'] = KW['js'] + """interface type enum readonly implements declare as satisfies keyof typeof infer
    is namespace abstract private protected public override never unknown asserts out""".split()
TY = {
 'cpp': "u8 u16 u32 i8 usize size_t uint8_t uint32_t int32_t FILE".split(),
 'js': """Math JSON Array Object Number String Boolean Promise Map Set Float32Array Int32Array Uint8Array
    WebAssembly console document window navigator Date Error requestAnimationFrame performance""".split(),
 'make': [], 'sh': [], 'json': [],
 'go': """string int int8 int16 int32 int64 uint uint8 uint16 uint32 uint64 byte rune float32 float64
    bool error any make new len cap append copy delete panic recover print println""".split(),
 'py': """int str bytes bytearray float bool list dict set tuple len range enumerate zip sorted min max
    sum abs print isinstance super object Exception ValueError asyncio json struct base64 hashlib""".split(),
}
# 원시 타입은 키워드가 아니라 '타입' 색이다 — 선언부에서 눈이 먼저 가야 할 곳이다.
TY['ts'] = TY['js'] + """number string boolean symbol bigint void any object Record Partial Readonly
    Pick Omit Exclude Extract Required NonNullable ReturnType Uint8Array Uint16Array Int8Array
    ArrayBuffer DataView WebSocket Buffer Uint32Array""".split()
COMMENT = {'cpp': r'//[^\n]*|/\*.*?\*/', 'js': r'//[^\n]*|/\*.*?\*/', 'ts': r'//[^\n]*|/\*.*?\*/',
           'make': r'#[^\n]*', 'sh': r'#[^\n]*', 'json': r'(?!x)x', 'txt': r'(?!x)x',
           'go': r'//[^\n]*|/\*.*?\*/', 'py': r'#[^\n]*'}

# 파이썬은 삼중따옴표 문자열을 먼저 잡아야 한다. 안 그러면 """ 가 빈 문자열 두 개로 쪼개진다.
STRPAT = {'py': r'"""(?:\\.|[^\\])*?"""|\'\'\'(?:\\.|[^\\])*?\'\'\''
                r'|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
          'go': r'`[^`]*`|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''}

def highlight(src, lang):
    lang = {'c++': 'cpp', 'c': 'cpp', 'mjs': 'js', 'javascript': 'js', 'golang': 'go',
            'python': 'py', 'makefile': 'make', 'shell': 'sh', 'bash': 'sh',
            'typescript': 'ts', 'tsx': 'ts', 'mts': 'ts'}.get(lang, lang)
    if lang not in KW:
        return html.escape(src)
    kw, ty = set(KW[lang]), set(TY[lang])
    pat = re.compile(
        r'(?P<cm>' + COMMENT[lang] + r')'
        r'|(?P<st>' + STRPAT.get(lang, r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`') + r')'
        r'|(?P<pp>^[ \t]*#[A-Za-z_]+|^[ \t]*\$(?= ))'
        r'|(?P<nb>\b0[xX][0-9a-fA-F_]+\b|\b\d[\d_]*\.?\d*(?:[eE][-+]?\d+)?[fuU]?\b)'
        r'|(?P<fn>\b[A-Za-z_]\w*(?=\s*\())'
        r'|(?P<id>\b[A-Za-z_]\w*\b)',
        re.S | re.M)
    out, pos = [], 0
    for m in pat.finditer(src):
        out.append(html.escape(src[pos:m.start()]))
        pos = m.end()
        t = m.lastgroup
        txt = html.escape(m.group())
        if t == 'id':
            if m.group() in kw:   out.append('<i class="kw">%s</i>' % txt)
            elif m.group() in ty: out.append('<i class="ty">%s</i>' % txt)
            else:                 out.append(txt)
        elif t == 'fn':
            if m.group() in kw:   out.append('<i class="kw">%s</i>' % txt)
            elif m.group() in ty: out.append('<i class="ty">%s</i>' % txt)
            else:                 out.append('<i class="fn">%s</i>' % txt)
        else:
            out.append('<i class="%s">%s</i>' % (t, txt))
    out.append(html.escape(src[pos:]))
    return ''.join(out)
