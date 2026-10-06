// 슬라이드 p14-v13-ri-unscoped — 인터페이스의 [UnscopedRef], C# 13.0
using System;
using System.Diagnostics.CodeAnalysis;

interface ICell
{
    [UnscopedRef] ref int Own { get; }   // may point into the receiver
    ref int Target { get; }
}

ref struct Cell : ICell
{
    int own;
    ref int target;                      // C# 11 ref field
    public Cell(ref int t) { target = ref t; own = 1; }
    [UnscopedRef] public ref int Own => ref own;
#if BAD2
    [UnscopedRef]
#endif
    public ref int Target => ref target;
}

class App
{
    static ref int Pick<T>(T t) where T : ICell, allows ref struct
#if BAD
        => ref t.Own;      // may return a ref to the parameter t
#else
        => ref t.Target;
#endif

    static void Main()
    {
        int x = 5;
        Pick(new Cell(ref x)) = 50;
        Console.WriteLine(x);
        var c = new Cell(ref x);
        c.Own += 10;
        Console.WriteLine(c.Own);
    }
}
