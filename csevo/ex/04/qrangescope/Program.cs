// 슬라이드 p4-v3-query-scope — 범위 변수의 이름이 겹치면, C# 3.0
using System;
using System.Linq;

class Program
{
    static void Main()
    {
        int[] xs = { 1, 2, 3 };
        int x = 0;

        var a = from x in xs select x * 2;
        var b = from y in xs
                from y in xs
                select y;
        Console.WriteLine(x + a.Count() + b.Count());
    }
}
