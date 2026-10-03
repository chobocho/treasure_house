// 슬라이드 p11-v10-st-this — this() 로 시작하는 생성자, C# 10.0
using System;

struct Grid
{
    public int Cols = 8;
    public int Rows;
    public string Name;

    public Grid(string name) : this()   // zero all, then initializers
    {
        Name = name;
    }

    public Grid(int rows)               // no this(): assign all
    {
        Rows = rows;
        Name = "r" + rows;
    }
}

class App
{
    static void Main()
    {
        var a = new Grid("a");
        var b = new Grid(3);
        Console.WriteLine(a.Cols + " " + a.Rows + " " + a.Name);
        Console.WriteLine(b.Cols + " " + b.Rows + " " + b.Name);
    }
}
