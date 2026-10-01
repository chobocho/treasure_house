// 슬라이드 p4-v3-ext-ref — ref this 확장 메서드, C# 7.2
using System;

struct Counter
{
    public int N;
}

static class CounterExt
{
    // this ref: c is the caller's variable, not a copy
    public static void Bump(this ref Counter c) { c.N++; }
}

class App
{
    static void Main()
    {
        Counter c = new Counter();
        c.Bump();
        c.Bump();
        Console.WriteLine("N = " + c.N);
    }
}
