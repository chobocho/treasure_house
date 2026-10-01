// 슬라이드 p3-v2-sort-trap — 비교할 줄 모르는 T 의 Sort, C# 2.0
using System;
using System.Collections.Generic;

class Point
{
    public int X;
    public Point(int x) { X = x; }
}

class App
{
    static void Main()
    {
        List<Point> ps = new List<Point>();
        ps.Add(new Point(2));
        ps.Add(new Point(1));
        try
        {
            ps.Sort();                    // compiles: no constraint
        }
        catch (InvalidOperationException e)
        {
            Console.WriteLine(e.Message);
            Console.WriteLine(e.InnerException.Message);
        }
    }
}
