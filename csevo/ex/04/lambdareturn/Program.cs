// 슬라이드 p4-v3-lambda-return — 문 본문 람다의 return, C# 3.0
using System;

class App
{
    static void Main()
    {
        Func<int, string> sign = x =>
        {
            if (x > 0) return "+";
            if (x < 0) return "-";
        };
        Func<int> answer = () => "42";
        Console.WriteLine(sign(1) + answer());
    }
}
