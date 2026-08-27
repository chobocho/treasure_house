# -*- coding: utf-8 -*-
"""hl.py — 덱 코드 블록용 최소 구문 강조기.
부 1 덱이 쓰는 클래스(.cm .kw .ty .st .nb .fn .pp)를 그대로 낸다."""
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
}
TY = {
 'cpp': "u8 u16 u32 i8 usize size_t uint8_t uint32_t int32_t FILE".split(),
 'js': """Math JSON Array Object Number String Boolean Promise Map Set Float32Array Int32Array Uint8Array
    WebAssembly console document window navigator Date Error requestAnimationFrame performance""".split(),
 'make': [], 'sh': [], 'json': [],
}
COMMENT = {'cpp': r'//[^\n]*|/\*.*?\*/', 'js': r'//[^\n]*|/\*.*?\*/',
           'make': r'#[^\n]*', 'sh': r'#[^\n]*', 'json': r'(?!x)x', 'txt': r'(?!x)x'}

def highlight(src, lang):
    lang = {'c++': 'cpp', 'c': 'cpp', 'mjs': 'js', 'javascript': 'js',
            'makefile': 'make', 'shell': 'sh', 'bash': 'sh'}.get(lang, lang)
    if lang not in KW:
        return html.escape(src)
    kw, ty = set(KW[lang]), set(TY[lang])
    pat = re.compile(
        r'(?P<cm>' + COMMENT[lang] + r')'
        r'|(?P<st>"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`)'
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
