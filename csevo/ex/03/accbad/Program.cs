// 슬라이드 p3-v2-accessor-rules — 접근자 한정자의 규칙, C# 2.0
using System;

class C
{
    int v;

    internal int A                       // public is wider
    { get { return v; } public set { v = value; } }

    public int B                         // both accessors
    { private get { return v; } private set { v = value; } }

    public int D                         // only one accessor
    { private get { return v; } }
}

class App
{
    static void Main() { }
}
