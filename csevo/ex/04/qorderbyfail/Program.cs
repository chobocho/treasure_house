// 슬라이드 p4-v3-query-orderby-trap — 비교할 수 없는 키, C# 3.0
using System;
using System.Linq;

class Box
{
    public int W;
    public Box(int w) { W = w; }
}

class Program
{
    static void Main()
    {
        Box[] boxes = { new Box(3), new Box(1) };
        var q = from b in boxes orderby b select b.W;   // compiles
        try
        {
            Console.WriteLine(string.Join(" ", q));
        }
        catch (InvalidOperationException e)
        {
            Console.WriteLine(e.Message);
            Console.WriteLine("  inner: " + e.InnerException.Message);
        }
        var ok = from b in boxes orderby b.W select b.W;
        Console.WriteLine(string.Join(" ", ok));
    }
}
