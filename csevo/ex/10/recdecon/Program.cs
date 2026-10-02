// 슬라이드 p10-v9-rec-decon — 레코드의 Deconstruct, C# 9.0
using System;

record Point(int X, int Y);
record Size
{
    public int W { get; init; }
    public int H { get; init; }
}

class App
{
    static string Where(Point p) => p switch
    {
        (0, 0) => "origin",                  // positional pattern
        (var x, 0) => "x-axis at " + x,
        _ => "elsewhere",
    };

    static void Main()
    {
        var (x, y) = new Point(3, 4);        // deconstruction
        Console.WriteLine(x + y);
        Console.WriteLine(Where(new Point(5, 0)));
        Size s = new Size { W = 2, H = 3 };
        Console.WriteLine(
            typeof(Size).GetMethod("Deconstruct") == null);
        Console.WriteLine(s is { W: 2 });    // property pattern works
    }
}
