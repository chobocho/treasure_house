// 슬라이드 p8-v7-pat-generic — 형식 매개변수에 패턴, C# 7.0
using System;

class App
{
    static string M<T>(T value)
    {
        if (value is int n) return "int " + n;      // open type T
        return "other " + value;
    }

    static void Main()
    {
        Console.WriteLine(M(5));
        Console.WriteLine(M("x"));
    }
}
