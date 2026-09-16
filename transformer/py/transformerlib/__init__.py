# -*- coding: utf-8 -*-
"""transformerlib — 밑바닥부터 만드는 트랜스포머의 파이썬 참조 구현.

numpy 도 torch 도 부르지 않는다(PLAN.md §9 결정 2). 곱셈 하나하나가
보이게 짜는 것이 이 패키지의 목적이다. 같은 식을 c/ 가 float32 로 다시
짜고, 두 구현은 SPEC.md 의 약속으로 서로를 검사한다.
"""
