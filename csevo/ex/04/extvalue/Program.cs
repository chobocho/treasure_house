// 슬라이드 p4-v3-ext-value — 값 형식 수신자는 복사본으로 간다, C# 3.0
using System;

struct Counter
{
    public int N;
}

static class CounterExt
{
    public static void Bump(this Counter c) { c.N++; }  // bumps a copy
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
