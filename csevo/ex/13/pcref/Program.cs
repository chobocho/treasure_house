// 슬라이드 p13-v12-pc-ref — ref · in 매개변수는 포착할 수 없다, C# 12.0
using System;

class Snap(in int v, ref int counter)
{
    public int Value = v;                  // read in an initializer
    public int Ticket = counter++;         // ref: writes the caller's
#if CAP
    public int Again() => v;               // capture an in parameter
#endif
}

class App
{
    static void Main()
    {
        int n = 1;
        var a = new Snap(42, ref n);
        var b = new Snap(43, ref n);
        Console.WriteLine($"{a.Value} {a.Ticket} {b.Ticket} n={n}");
    }
}
