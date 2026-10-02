// 슬라이드 p9-v8-pospat — 위치 패턴과 Deconstruct, C# 8.0
using System;

class Cell
{
    public int Row { get; }
    public int Col { get; }
    public Cell(int r, int c) { Row = r; Col = c; }
    public void Deconstruct(out int row, out int col)
    {
        row = Row;
        col = Col;
    }
}

class App
{
    // a chess-like 8x8 board seen from (row, col)
    static string Where(Cell c) => c switch
    {
        (0, 0) => "corner a1",
        (0, _) => "first rank",
        (_, 0) => "a-file",
        var (r, k) when r == k => "diagonal " + r,
        var (r, k) when r > 7 || k > 7 => "off board",
        _ => "inside",
    };

    static void Main()
    {
        var cells = new[]
        {
            new Cell(0, 0), new Cell(0, 5), new Cell(3, 0),
            new Cell(4, 4), new Cell(9, 2), new Cell(2, 5),
        };
        foreach (Cell c in cells)
            Console.WriteLine("({0},{1}) {2}", c.Row, c.Col, Where(c));
    }
}
