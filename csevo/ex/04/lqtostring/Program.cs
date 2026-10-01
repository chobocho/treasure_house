// 슬라이드 p4-v3-linq-tostring — 쿼리를 찍으면 형식 이름, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static void Main()
    {
        int[] xs = { 1, 2, 3 };
        List<int> list = new List<int>(xs);

        Console.WriteLine(xs.Where(x => x > 1));
        Console.WriteLine(xs.Where(x => x > 1).Select(x => x * 2));
        Console.WriteLine(list.Select(x => x * 2));
        Console.WriteLine(string.Join(", ", xs.Where(x => x > 1)));
    }
}
