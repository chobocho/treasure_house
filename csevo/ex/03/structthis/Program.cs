// 슬라이드 p3-v2-capture-limits — 구조체의 this 를 베껴서 잡기, C# 2.0
using System;

delegate int D();

struct Cell
{
    public int Value;

    public D Getter()
    {
        Cell copy = this;                      // this itself: CS1673
        return delegate { return copy.Value; };
    }
}

class App
{
    static void Main()
    {
        Cell c = new Cell();
        c.Value = 1;
        D get = c.Getter();
        c.Value = 2;                           // the copy won't see it
        Console.WriteLine(c.Value + " " + get());
    }
}
