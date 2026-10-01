// 슬라이드 p4-v3-linq-distinct — Distinct 는 Equals 로 고른다, C# 3.0
using System;
using System.Linq;

class Point
{
    public int X, Y;
    public Point(int x, int y) { X = x; Y = y; }
}

class Program
{
    static void Main()
    {
        int[] xs = { 3, 1, 3, 2, 1 };
        Console.WriteLine(string.Join(" ", xs.Distinct()));

        var anon = new[] {
            new { X = 1, Y = 2 }, new { X = 1, Y = 2 },
            new { X = 3, Y = 4 }
        };
        Console.WriteLine("anonymous: " + anon.Distinct().Count());

        Point[] pts = {
            new Point(1, 2), new Point(1, 2), new Point(3, 4)
        };
        Console.WriteLine("class:     " + pts.Distinct().Count());
    }
}
