// 슬라이드 p12-v11-sa-virtual — static virtual 과 기본 구현, C# 11.0
using System;

interface IAdd<TSelf> where TSelf : IAdd<TSelf>
{
    static abstract TSelf operator +(TSelf a, TSelf b);
    // A default body may call other static members through TSelf
    static virtual TSelf Twice(TSelf x) => x + x;
}

struct Cm : IAdd<Cm>                  // keeps the default Twice
{
    public int V;
    public static Cm operator +(Cm a, Cm b) => new Cm { V = a.V + b.V };
}

struct Loud : IAdd<Loud>              // replaces it
{
    public int V;
    public static Loud operator +(Loud a, Loud b) =>
        new Loud { V = a.V + b.V };
    public static Loud Twice(Loud x) => new Loud { V = -1 };
}

class App
{
    static T Tw<T>(T x) where T : IAdd<T> => T.Twice(x);

    static void Main()
    {
        Console.WriteLine(Tw(new Cm { V = 4 }).V);
        Console.WriteLine(Tw(new Loud { V = 4 }).V);
#if BAD
        Console.WriteLine(Cm.Twice(new Cm()).V);  // not a member of Cm
#endif
    }
}
