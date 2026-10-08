# -*- coding: utf-8 -*-
"""1부 — 탄생 이전(1996–2002)의 증거. 예제는 ex/01/ 아래에 있다.

1부는 버전 부가 아니다. 그래서 언어 버전 짝(가) 대신, 설계자들이 말한
결정을 두 언어로 돌려 본다 — 같은 생각을 C# 1(-langversion:1)과 자바로
적고, 두 컴파일러가 각각 무엇을 받고 무엇을 거절하는지를 캡처한다.

자바 쪽(ex/01/<예제>/java/)은 이 기계의 OpenJDK 21 로 돈다. 툴체인에
자바 실행기가 없으므로 jrun() 이 javac·java 를 직접 부른다:

  · 예제의 java/ 를 scratch/work/<캡처 이름>/ 에 베끼고, 단계(명령 줄)를
    차례로 돌린다. 셸은 쓰지 않는다. cp·ls 같은 단계도 진짜 명령이다.
  · javac·java 는 dotnet 과 같은 잠금(scratch/dotnet.lock)을 잡는다 —
    이 기계는 JVM 이든 CLR 이든 한 번에 하나만 버틴다(PLAN.md §0.8).
  · JVM 에는 늘 -Xmx256m · -XX:+UseSerialGC 를 붙인다(javac·javap 는 -J 로).
    캡처의 '$' 줄에는 이 두 플래그를 적지 않는다 — 출력에 아무 영향이
    없는 메모리 설정이고, 여기 한 곳에 밝혀 둔다.
  · 캡처 이름은 out/01-<예제>__java[-<tag>].txt, 첫 줄은 '$ <명령>'.
    단계가 0 이 아닌 코드로 끝나면 그 뒤에 '[exit N]' 을 적는다.

시간 O(단계 수) — JVM 하나가 이 기계에서 2–5초다."""
import os
import subprocess

import csver   # run_all.py 가 tools/ 를 sys.path 에 넣어 둔다

EX = 'ex/01/'
JVM = ['-Xmx256m', '-XX:+UseSerialGC']


def jargv(words):
    """화면의 명령 → 실제 argv. JVM 메모리 플래그만 끼운다."""
    if words[0] in ('javac', 'javap'):
        return words[:1] + ['-J' + f for f in JVM] + words[1:]
    if words[0] == 'java':
        return ['java'] + JVM + words[1:]
    return words


def jrun(ctx, slug, steps, tag=None, expect=0):
    """ex/01/<slug>/java/ 에서 steps 를 차례로 돌려 캡처한다.
    expect 는 마지막 단계의 종료 코드다(다르면 멈춘다)."""
    src = os.path.join(csver.BASE, EX + slug, 'java')
    name = '01-%s__java%s' % (slug, '-' + tag if tag else '')
    work = os.path.join(csver.SCRATCH, 'work', name)
    csver.prepare(src, work)
    env = csver.env_for(csver.SCRATCH)
    lines, code = [], 0
    for step in steps:
        lines.append('$ ' + step)
        words = step.split()
        if words[0] in ('javac', 'javap', 'java'):
            p = csver._run(jargv(words), work, env)
        else:
            p = subprocess.run(words, cwd=work, env=env,
                               stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=60)
        text = csver.normalise(p.stdout.decode('utf-8', 'replace'), work,
                               csver.SCRATCH).rstrip('\n')
        if text:
            lines.append(text)
        code = p.returncode
        if code:
            lines.append('[exit %d]' % code)
    if code != expect:
        raise RuntimeError('[p01] %s (%s) → 종료 %d, 기대 %d\n%s'
                           % (slug, tag or 'java', code, expect,
                              '\n'.join(lines)))
    ctx.save(name + '.txt', '\n'.join(lines) + '\n')


def run(ctx):
    # 1장 — 자바와 J++
    jrun(ctx, 'sunbutton', ['javac -version', 'javac Main.java',
                            'java Main'])
    ctx.cs(EX + 'wfc')
    jrun(ctx, 'wfc', ['javac SimpleForm.java'], expect=1)
    ctx.cs(EX + 'adapters')
    jrun(ctx, 'adapters', ['javac Editor.java', 'ls', 'java Editor'])

    # 3장 — .NET 발표: IL 의 add 와 바이트코드의 iadd·ladd·dadd
    ctx.cs(EX + 'iladd', flags='-optimize+')
    jrun(ctx, 'iladd', ['javac Add.java', 'javap -c Add'])

    # 4장 — 설계 결정을 코드로
    # 검사 예외
    jrun(ctx, 'checked', ['javac Main.java'], expect=1)
    ctx.cs(EX + 'checked')
    jrun(ctx, 'throwsver', ['javac Exc.java Lib.java Client.java',
                            'java Client',
                            'cp v2/Lib.java Lib.java',
                            'javac Lib.java',
                            'java Client',
                            'javac Client.java'], expect=1)
    jrun(ctx, 'throwsall', ['javac Main.java', 'java Main'])
    # 가상 메서드와 버전 관리
    jrun(ctx, 'virtver', ['javac Base.java Derived.java Main.java',
                          'java Main',
                          'cp v2/Base.java Base.java',
                          'javac Base.java',
                          'java Main',
                          'javac Derived.java'])
    jrun(ctx, 'virtret', ['javac Base.java Derived.java Main.java',
                          'java Main',
                          'cp v2/Base.java Base.java',
                          'javac Base.java',
                          'java Main',
                          'javac Derived.java'], expect=1)
    ctx.cs(EX + 'virtcs')
    ctx.cs(EX + 'virtcs', flags='-define:OVERRIDE', tag='override')
    # 오버로드 해석
    ctx.cs(EX + 'overderived')
    jrun(ctx, 'overderived', ['javac Main.java', 'java Main'])
    # 대리자
    jrun(ctx, 'twosource', ['javac Dialog.java', 'java Dialog',
                            'javac Modern.java', 'java Modern',
                            'javac Twice.java'], expect=1)
    ctx.cs(EX + 'twosource')
    ctx.cs(EX + 'delcall')
    jrun(ctx, 'delcall', ['javac Main.java', 'java Main'])
    # 통합 형식 체계
    ctx.cs(EX + 'unified')
    jrun(ctx, 'unified', ['javac Wrap.java', 'java Wrap',
                          'javac Prim.java'], expect=1)
    # 컴포넌트 — 속성·이벤트·특성
    ctx.cs(EX + 'beans')
    jrun(ctx, 'beans', ['javac Main.java', 'java Main'])
