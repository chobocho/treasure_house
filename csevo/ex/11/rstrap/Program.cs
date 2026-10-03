// 슬라이드 p11-v10-rs-trap — 바뀌는 record struct 를 키로 쓰면, C# 10.0
using System;
using System.Collections.Generic;

record struct Cell(int Row, int Col);

class App
{
    static void Main()
    {
        var c = new Cell(1, 1);
        var seen = new HashSet<Cell> { c };
        c.Row = 2;                          // the local copy only
        Console.WriteLine(seen.Contains(c) + " "
            + seen.Contains(new Cell(1, 1)));
        var cells = new List<Cell> { new Cell(0, 0) };
        var first = cells[0];               // a copy
        first.Col = 5;
        Console.WriteLine(cells[0] + " " + first);
#if BAD
        cells[0].Col = 5;
#endif
    }
}
