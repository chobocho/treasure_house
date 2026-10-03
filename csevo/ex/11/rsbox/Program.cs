// 슬라이드 p11-v10-rs-box — Equals 가 상자를 만드는가, C# 10.0
using System;

struct PlainPt
{
    public int X, Y;
    public PlainPt(int x, int y) { X = x; Y = y; }
}

record struct RecPt(int X, int Y);

class App
{
    static string Allocates(Func<bool> f)
    {
        f();                                        // warm up
        long before = GC.GetAllocatedBytesForCurrentThread();
        for (int i = 0; i < 1000; i++) f();
        long after = GC.GetAllocatedBytesForCurrentThread();
        return after > before ? "allocates" : "no allocation";
    }

    static void Main()
    {
        var p1 = new PlainPt(1, 2);
        var p2 = new PlainPt(1, 2);
        var r1 = new RecPt(1, 2);
        var r2 = new RecPt(1, 2);
        Func<bool> plain = () => p1.Equals(p2);
        Func<bool> rec = () => r1.Equals(r2);
        Console.WriteLine("struct        " + Allocates(plain));
        Console.WriteLine("record struct " + Allocates(rec));
    }
}
