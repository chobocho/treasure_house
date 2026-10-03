// 슬라이드 p12-v11-sa-typearg — 형식 인수가 못 되는 인터페이스, C# 11.0
using System;
using System.Collections.Generic;

interface IZero<T> where T : IZero<T>
{
    static abstract T Zero { get; }               // no body
}

interface IHello
{
    static virtual string Hi => "default hi";     // has a body
}

struct Cm : IZero<Cm>, IHello
{
    public static Cm Zero => new Cm();
}

class App
{
    static string H<T>() where T : IHello => T.Hi;

    static void Main()
    {
        var ok = new List<IHello>();               // allowed
        Console.WriteLine(H<Cm>() + " / " + H<IHello>());
#if BAD
        var bad = new List<IZero<Cm>>();
#endif
    }
}
