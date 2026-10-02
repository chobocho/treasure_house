// 슬라이드 p10-v9-rec-eqref — 필드마다 EqualityComparer, C# 9.0
using System;
using System.Collections.Generic;

record Order(string Id, int[] Lines, List<string> Tags);

class App
{
    static void Main()
    {
        var o1 = new Order("A", new[] { 1, 2 },
            new List<string> { "x" });
        var o2 = new Order("A", new[] { 1, 2 },
            new List<string> { "x" });
        Console.WriteLine(o1 == o2);
        Console.WriteLine(o1.Id.Equals(o2.Id));
        Console.WriteLine(o1.Lines.Equals(o2.Lines));
        var o3 = o1 with { Id = "A" };      // shares Lines and Tags
        Console.WriteLine(o1 == o3);
        Console.WriteLine(o1);
    }
}
