// 슬라이드 p8-v7-decon-nest — 겹친 분해와 foreach, C# 7.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        var (name, (x, y)) = ("home", (1, 2));     // nested
        Console.WriteLine(name + " " + (x + y));

        var moves = new List<(string who, (int dx, int dy) d)>
        {
            ("A", (1, 0)), ("B", (0, -1)),
        };
        foreach (var (who, (dx, dy)) in moves)    // in foreach
            Console.WriteLine(who + ": " + dx + "," + dy);

        var (a, b) = (1, "one");                  // mixed types
        Console.WriteLine(b + "=" + a);
    }
}
