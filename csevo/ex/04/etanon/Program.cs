// 슬라이드 p4-v3-et-anon — 익명 형식과 초기화자도 마디가 된다, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq.Expressions;

class Point { public int X { get; set; } public int Y { get; set; } }

class Program
{
    static void Main()
    {
        Expression<Func<int, object>> anon = x => new { x, Sq = x * x };
        Expression<Func<int, Point>> init =
            x => new Point { X = x, Y = -x };
        Expression<Func<int, List<int>>> list =
            x => new List<int> { x, x + 1 };

        Console.WriteLine(anon.Body.NodeType + "  " + anon);
        Console.WriteLine(init.Body.NodeType + "  " + init);
        Console.WriteLine(list.Body.NodeType + "  " + list);
    }
}
