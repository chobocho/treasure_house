// 슬라이드 p11-v10-rs-equality — 구조체와 record struct, C# 10.0
using System;

struct PlainPt
{
    public int X, Y;
    public PlainPt(int x, int y) { X = x; Y = y; }
}

record struct RecPt(int X, int Y);

class App
{
    static void Main()
    {
        var p1 = new PlainPt(1, 2);
        var p2 = new PlainPt(1, 2);
        Console.WriteLine(p1.Equals(p2));          // ValueType.Equals
        Console.WriteLine(typeof(IEquatable<PlainPt>)
            .IsAssignableFrom(typeof(PlainPt)));
#if BAD
        Console.WriteLine(p1 == p2);               // no operator
#endif
        var r1 = new RecPt(1, 2);
        var r2 = new RecPt(1, 2);
        Console.WriteLine(r1.Equals(r2));          // Equals(RecPt)
        Console.WriteLine(typeof(IEquatable<RecPt>)
            .IsAssignableFrom(typeof(RecPt)));
        Console.WriteLine(r1 == r2);               // synthesized ==
    }
}
