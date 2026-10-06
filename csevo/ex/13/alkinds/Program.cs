// 슬라이드 p13-v12-al-kinds — 배열 · 기본 형식 · int?, C# 12.0
using System;
using System.Collections.Generic;
using Grid = int[,];
using Bytes = byte[];
using Num = double;
using MaybeInt = int?;
using Lookup = System.Collections.Generic.Dictionary<string, int[]>;

class App
{
    static void Main()
    {
        Grid g = new int[2, 3];
        Bytes b = [1, 2, 3];
        Num half = 0.5;
        MaybeInt none = null;
        var map = new Lookup { ["a"] = [1, 2] };
        Console.WriteLine($"{g.Rank} {g.Length} {b.Length} {half}");
        Console.WriteLine($"{none.HasValue} {map["a"].Length}");
        Console.WriteLine(typeof(Num).FullName);
        List<Num> list = [half];
        Console.WriteLine(list.GetType().Name);
    }
}
