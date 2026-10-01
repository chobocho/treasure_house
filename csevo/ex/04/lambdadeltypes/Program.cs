// 슬라이드 p4-v3-lambda-deltypes — 서로 바꿀 수 없는 대리자, C# 3.0
using System;

class App
{
    static void Main()
    {
        Predicate<int> p = x => x > 0;          // the same lambda text…
        Func<int, bool> f = x => x > 0;         // …fits both types
        Func<int, bool> g = p;             // but the types do not mix
        Console.WriteLine(f(1) + " " + g(1));
    }
}
