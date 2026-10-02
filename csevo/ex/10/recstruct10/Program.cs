// 슬라이드 p10-v9-rec-struct10 — record struct, C# 10.0
using System;

record struct Point(int X, int Y);           // mutable properties
readonly record struct Size(int W, int H);   // init properties
record class Person(string Name);            // = record

class App
{
    static void Main()
    {
        var p = new Point(1, 2);
        p.X = 10;                            // set, not init
        Console.WriteLine(p);
        Console.WriteLine(p == new Point(10, 2));
        var s = new Size(3, 4);
        Console.WriteLine(s with { H = 5 });
        Console.WriteLine(typeof(Point).IsValueType + " "
            + typeof(Person).IsValueType);
    }
}
