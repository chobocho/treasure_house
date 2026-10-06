// 슬라이드 p13-v12-rr-why — in 이 임시 변수를 조용히 받는다, C# 11.0
using System;

// a view that keeps a reference to its argument (C# 11 ref field)
ref struct View
{
    readonly ref readonly int _r;
    public View(in int r) { _r = ref r; }
    public int Value => _r;
}

class App
{
    static void Main()
    {
        int x = 1;
        var a = new View(in x);    // reference to x
        var b = new View(x);       // also x - 'in' may be omitted
        var c = new View(x + 0);   // reference to a hidden temporary
        var d = new View(5);       // same
        x = 42;
        Console.WriteLine($"{a.Value} {b.Value} {c.Value} {d.Value}");
    }
}
