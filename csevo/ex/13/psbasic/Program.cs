// 슬라이드 p13-v12-primary-struct — 구조체의 기본 생성자, C# 12.0
using System;

struct Size(int w, int h)
{
    public int Area => w * h;
    public override string ToString() => $"{w}x{h}";
}

struct Cell(int row, int col)
{
    public Cell() : this(1, 1) { }           // C# 10 parameterless
    public override string ToString() => $"R{row}C{col}";
}

class App
{
    static void Main()
    {
        Console.WriteLine($"{new Size(3, 4)} {new Size(3, 4).Area}");
        Console.WriteLine($"{new Size()} {default(Size)}");
        Console.WriteLine($"{new Cell()} {default(Cell)}");
        var arr = new Cell[1];
        Console.WriteLine(arr[0]);
    }
}
