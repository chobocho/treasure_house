// 슬라이드 p8-v7-discard-lambda9 — 람다의 버리기 매개변수, C# 9.0
using System;

class App
{
    static void Main()
    {
        Func<int, int, int> zero = (_, _) => 0;     // two discards
        Console.WriteLine(zero(1, 2));
        Func<int, int> twice = _ => _ * 2;          // one '_': a name
        Console.WriteLine(twice(21));
    }
}
