// 슬라이드 p5-v4-opt-lambda — 뒤 버전: 람다의 기본값, C# 12.0
using System;

class Program
{
    static void Main()
    {
        var add = (int x, int by = 1) => x + by;
        Console.WriteLine(add(10));
        Console.WriteLine(add(10, 5));
        Console.WriteLine(add.Method.GetParameters()[1].DefaultValue);
    }
}
