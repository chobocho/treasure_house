// 슬라이드 p4-v3-objinit-nested — 값 형식 속성은 안 된다, C# 3.0
using System;

struct Pt
{
    public int X, Y;
}

class Sprite
{
    Pt pos;
    public Pt Pos { get { return pos; } set { pos = value; } }
}

class App
{
    static void Main()
    {
        Sprite s = new Sprite { Pos = { X = 1, Y = 2 } };
        Console.WriteLine(s.Pos.X);
    }
}
