// 슬라이드 p11-v10-st-public — public 이어야 한다, C# 10.0
using System;

struct Hidden
{
    public int X;
    private Hidden() { X = 42; }            // not public
}

class App
{
    static void Main() => Console.WriteLine(new Hidden().X);
}
