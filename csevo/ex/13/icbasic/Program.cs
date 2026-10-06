// 슬라이드 p13-v12-intercept — 인터셉터(미리 보기), C# 12.0
using System;

class App
{
    static void Main()
    {
        Console.WriteLine(Calc.Twice(21));   // line 8, column 32
        Console.WriteLine(Calc.Twice(4));    // not intercepted
    }
}

static class Calc
{
    public static int Twice(int x) => x * 2;
}
