// 슬라이드 p10-v9-rec-mutable — 바뀌는 레코드를 사전 키로, C# 9.0
using System;
using System.Collections.Generic;

record Cell
{
    public int Row { get; set; }             // set, not init
    public int Col { get; set; }
}

class App
{
    static void Main()
    {
        var key = new Cell { Row = 1, Col = 1 };
        var map = new Dictionary<Cell, string> { [key] = "x" };
        Console.WriteLine(map.ContainsKey(key));
        key.Row = 2;                         // hash code changes
        Console.WriteLine(map.ContainsKey(key));
        var same = new Cell { Row = 1, Col = 1 };
        Console.WriteLine(map.ContainsKey(same));
        Console.WriteLine(map.Count);
        foreach (var pair in map)
            Console.WriteLine(pair.Key + " -> " + pair.Value);
    }
}
