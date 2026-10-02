// 슬라이드 p8-v7_2-refstruct-capture — 람다·지역 함수의 포착, C# 7.2
using System;

class App
{
    static void Main()
    {
        Span<int> s = new int[3];
        Func<int> f = () => s.Length;      // a lambda
        int Len() => s.Length;             // a local function
        Console.WriteLine(f() + Len());
    }
}
