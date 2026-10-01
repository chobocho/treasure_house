# -*- coding: utf-8 -*-
"""0부 — 길잡이의 증거: 이 기계의 SDK·런타임, 언어 버전 게이트 한 짝."""


def run(ctx):
    # 이 덱의 첫째 심판 — 설치된 SDK 와 런타임
    ctx.cs('ex/00/machine', cmd='dotnet --version', tag='sdk')
    ctx.cs('ex/00/machine')
    # 같은 소스, 언어 버전만 다르게: 12 는 돌고 11 은 컴파일러가 거절한다
    ctx.cs('ex/00/gate')
    ctx.cs('ex/00/gate', v='11.0', expect=1)
    # C# 1(ISO-1) 문법만 쓴 프로그램 — 언어 버전은 1, 런타임은 10
    ctx.cs('ex/00/iso1')
    ctx.cs('ex/00/iso1', v='ISO-1', tag='iso')
