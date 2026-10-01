// 슬라이드 p4-v3-query-readonly — 범위 변수에는 대입할 수 없다, C# 3.0
using System;
using System.Linq;

class Program
{
    static void Main()
    {
        int[] xs = { 1, 2, 3 };
        var q = from x in xs
                where (x = x * 2) > 2
                select x;
        Console.WriteLine(q.Count());
    }
}
