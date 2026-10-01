// 슬라이드 p3-v2-inference-fail — 유추가 되는 경우, C# 2.0
using System;

class App
{
    static T Pick<T>(T a, T b) { return b; }
    static T Make<T>() { return default(T); }

    static void Main()
    {
        Console.WriteLine(Pick(1, 2L).GetType());   // int and long
        Console.WriteLine(Pick<object>(1, "a"));    // T written out
        Console.WriteLine(Make<int>());
    }
}
