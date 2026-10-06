// 슬라이드 p13-v12-refro — ref readonly 매개변수, C# 12.0
using System;

ref struct View
{
    readonly ref readonly int _r;
    public View(ref readonly int r) { _r = ref r; }
    public int Value => _r;
}

class App
{
    static readonly int Ro = 7;

    static void Main()
    {
        int x = 1;
        var a = new View(in x);    // read-only reference
        var b = new View(ref x);   // 'ref' is accepted too
        var c = new View(in Ro);   // readonly field: 'in' only
#if W1
        var w = new View(x);       // no annotation
#elif W2
        var w = new View(x + 0);   // not a variable
#elif W3
        var w = new View(Ro);      // readonly field, no 'in'
#else
        var w = a;
#endif
        x = 42;
        Console.WriteLine($"{a.Value} {b.Value} {c.Value} {w.Value}");
    }
}
