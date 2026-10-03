// 슬라이드 p12-v11-sc-unscoped — [UnscopedRef], C# 11
using System;
using System.Diagnostics.CodeAnalysis;

struct Counter
{
    int _count;
#if BAD
    public ref int Count => ref _count;       // this is scoped
#else
    [UnscopedRef] public ref int Count => ref _count;
#endif
    public override string ToString() => "count " + _count;
}

class Program
{
    static ref int Grab(ref Counter c) => ref c.Count;
#if BAD2
    static ref int Temp() => ref new Counter().Count;   // a temporary
#endif

    static void Main()
    {
        var c = new Counter();
        c.Count = 5;                 // write through the property
        Grab(ref c) += 10;
        ref int r = ref c.Count;
        r++;
        Console.WriteLine(c);
    }
}
