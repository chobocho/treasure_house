// 슬라이드 p2-v1-reimpl — 인터페이스 다시 구현하기, C# 1.0
using System;

interface IGreet { string Hello(); }

class Base : IGreet
{
    public string Hello() { return "Base"; }        // not virtual
}

class Hider : Base
{
    public new string Hello() { return "Hider"; }
}

class Reimpl : Base, IGreet                    // lists IGreet again
{
    public new string Hello() { return "Reimpl"; }
}

class App
{
    static void Show(Base b)
    {
        IGreet g = b;
        Console.WriteLine(b.GetType().Name.PadRight(7) + "Base ref: "
            + b.Hello() + ", IGreet ref: " + g.Hello());
    }

    static void Main()
    {
        Show(new Base());
        Show(new Hider());
        Show(new Reimpl());
    }
}
