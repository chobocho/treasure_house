// 슬라이드 p7-v6-struct-autoprop — 구조체 생성자와 자동 속성, C# 6.0
using System;

struct S
{
    public int X { get; set; }
    public int Y { get; set; }

    public S(int x, int y)
    {
        this.X = x;
        this.Y = y;
    }
}

class App
{
    static void Main()
    {
        S s = new S(3, 4);
        Console.WriteLine(s.X + " " + s.Y);
    }
}
