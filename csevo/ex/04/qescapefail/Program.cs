// 슬라이드 p4-v3-query-escape — 쿼리 안에서 @ 를 빼면, C# 3.0
using System;
using System.Linq;

class Program
{
    static void Main()
    {
        int[] into = { 1, 2, 3 };
        int[] big = (from x in into select x * 10).ToArray();
        Console.WriteLine(big[0]);
    }
}
