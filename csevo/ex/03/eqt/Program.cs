// 슬라이드 p3-v2-eq-trap — 제약 없는 T 에 == 를 쓰면, C# 2.0
using System;

class App
{
    static bool Same<T>(T a, T b)
    {
        return a == b;
    }

    static void Main()
    {
        Console.WriteLine(Same(1, 1));
    }
}
