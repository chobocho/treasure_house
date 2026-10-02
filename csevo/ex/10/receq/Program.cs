// 슬라이드 p10-v9-rec-equality — 값 동등성, C# 9.0
using System;
using System.Collections.Generic;

record Point(int X, int Y);

class App
{
    static void Main()
    {
        Point a = new Point(1, 2);
        Point b = new Point(1, 2);
        Console.WriteLine("a == b            " + (a == b));
        Console.WriteLine("a.Equals(b)       " + a.Equals(b));
        Console.WriteLine("Equals(object)    " + a.Equals((object)b));
        Console.WriteLine("ReferenceEquals   " + ReferenceEquals(a, b));
        Console.WriteLine("same hash         "
            + (a.GetHashCode() == b.GetHashCode()));
        var set = new HashSet<Point> { a, b };
        Console.WriteLine("HashSet count     " + set.Count);
        object oa = a, ob = b;
        Console.WriteLine("(object) ==       " + (oa == ob));
        Console.WriteLine("object.Equals     " + Equals(oa, ob));
        Point n = null;
        Console.WriteLine("null == null      " + (n == null));
        Console.WriteLine("a == null         " + (a == n));
    }
}
