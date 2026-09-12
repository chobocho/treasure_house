# -*- coding: utf-8 -*-
"""Adler-32 과 CRC-32 — SPEC §10.8.

압축과는 상관없는 물건인데 압축 컨테이너마다 붙어 있다. 압축은 한 비트만
어긋나도 전혀 다른 것이 풀려 나온다. 원본이 맞는지 볼 방법이
없으면 "풀렸다" 와 "제대로 풀렸다" 를 구별할 수 없다.

Adler-32 는 zlib 이, CRC-32 는 gzip 이 쓴다. 둘의 차이는 속도와 세기다 —
Adler 는 더하기 두 번이라 빠르고, 짧은 데이터에서 약하다. CRC 는 표를
한 번 만들어 두면 바이트당 XOR 과 시프트 한 번이고, 비트 오류 검출력이
이론적으로 보장된다. 그래서 gzip 쪽이 CRC 를 골랐다.

표는 다항식에서 직접 만든다. 256칸을 소스에 적어 두는 편이 빠르지만,
숫자 256개를 다섯 언어에 옮겨 적으면 어딘가는 틀린다.
"""
ADLER_MOD = 65521
# Adler 의 b 가 32비트를 넘기 전에 나눠야 하는 최대 블록. zlib 의 NMAX
# 다.
ADLER_NMAX = 5552
CRC_POLY = 0xEDB88320


def adler32(data):
    a, b = 1, 0
    for i in range(0, len(data), ADLER_NMAX):
        for byte in data[i:i + ADLER_NMAX]:
            a += byte
            b += a
        a %= ADLER_MOD
        b %= ADLER_MOD
    return ((b << 16) | a) & 0xFFFFFFFF


def _make_crc_table():
    table = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = (c >> 1) ^ (CRC_POLY if (c & 1) else 0)
        table.append(c)
    return table


CRC_TABLE = _make_crc_table()


def crc32(data):
    c = 0xFFFFFFFF
    for byte in data:
        c = CRC_TABLE[(c ^ byte) & 0xFF] ^ (c >> 8)
    return c ^ 0xFFFFFFFF
