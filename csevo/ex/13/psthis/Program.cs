// 슬라이드 p13-v12-ps-this — this 대입이 매개변수를 덮어쓴다, C# 12.0
using System;

struct Pos(int x)
{
    public int X => x;
    public void Become(Pos other) { this = other; }   // no warning
    public void Move() => x++;
}

class App
{
    static void Main()
    {
        var a = new Pos(1);
        var b = a;                 // a copy, captured field and all
        a.Move();
        Console.WriteLine($"a={a.X} b={b.X}");
        a.Become(new Pos(9));
        Console.WriteLine($"a={a.X}");
    }
}
