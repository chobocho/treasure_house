// 슬라이드 p11-v10-wi-tuple — 튜플도 구조체다, C# 10.0
using System;

class App
{
    static void Main()
    {
        var p = (Name: "ann", Age: 3);
        var q = p with { Age = 4 };         // ValueTuple is a struct
        var r = p with { Item1 = "bob" };   // element by position name
        Console.WriteLine(p + " " + q + " " + r);
        Console.WriteLine(q.GetType().Name);
    }
}
