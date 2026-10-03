// 슬라이드 p12-v11-fl-sig — file 형식이 나올 수 없는 곳, C# 11
#if BAD4
global using static Util;                // file type in global using
#endif
using System;

file class Util { public static int Twice(int x) => 2 * x; }

file interface IShape { double Area(); }

class Square : IShape                    // implementing is allowed
{
    public double Area() => 4;
}

file class Box
{
    public Util Make() => new Util();    // ok: inside a file type
}

#if BAD3
public file record R(int X);             // with an accessibility
#endif

class Program
{
#if BAD1
    public static Util Expose() => new Util();   // in a signature
#endif
#if BAD2
    file class Nested { }                // not top level
#endif
    static void Main()
    {
        IShape s = new Square();
        Console.WriteLine(Util.Twice(21) + " " + s.Area());
        Console.WriteLine(new Box().Make().GetType().Name.Length > 0);
    }
}
