// 슬라이드 p7-v6-dictinit-mix — 인덱서라면 무엇이든, C# 6.0
using System;
using System.Collections.Generic;

class Grid
{
    int[,] cells = new int[2, 2];
    public string Name { get; set; }
    public int this[int r, int c]
    {
        get { return cells[r, c]; }
        set { cells[r, c] = value; }
    }
}

class Program
{
    static void Main()
    {
        Grid g = new Grid { Name = "g", [0, 1] = 5, [1, 0] = 7 };
        Console.WriteLine(g.Name + " " + g[0, 1] + " " + g[1, 0]);
        try
        {
            var m = new Dictionary<string, List<int>> { ["a"] = { 1 } };
        }
        catch (KeyNotFoundException)
        {
            Console.WriteLine("[\"a\"] = { 1 } reads d[\"a\"] first");
        }
#if BAD
        var bad = new Dictionary<string, int> { ["a"] = 1, { "b", 2 } };
#endif
    }
}
