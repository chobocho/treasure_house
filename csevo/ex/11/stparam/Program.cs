// 슬라이드 p11-v10-st-param — 매개변수 기본값 new() 와 생성자, C# 10.0
using System;

struct Plain
{
    public int X;
    public Plain(int x) { X = x; }
}

struct WithCtor
{
    public int X;
    public WithCtor() { X = 1; }
}

class App
{
    static int A(Plain p = new()) => p.X;          // zeroed: a constant
#if BAD
    static int B(WithCtor w = new()) => w.X;   // runs code
#endif
    static int C(WithCtor w = default) => w.X;     // zeroed

    static void Main() => Console.WriteLine(A() + " " + C());
}
