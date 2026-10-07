// 슬라이드 p15-v14-brk-uref — 옛 ref 안전 규칙과 [UnscopedRef], C# 14
using System;
using System.Diagnostics.CodeAnalysis;

struct S
{
    public int F;
    [UnscopedRef] public ref int Ref() => ref F;   // C# 11 attribute
}

class Program
{
    static void Main()
    {
        var s = new S();
        s.Ref() = 42;
        Console.WriteLine(s.F);
    }
}
