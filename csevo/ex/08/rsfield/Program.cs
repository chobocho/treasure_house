// 슬라이드 p8-v7_2-refstruct-heap — 클래스의 필드가 되려 하면, C# 7.2
using System;

ref struct R { public int X; }

class Holder
{
    R field;                               // lives in a heap object
}

struct Plain
{
    Span<int> span;                        // an ordinary struct
}

class App
{
    static void Main() { }
}
