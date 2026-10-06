// 슬라이드 p14-v13-brk-inline — record struct 의 InlineArray, C# 13
using System;
using System.Runtime.CompilerServices;

[InlineArray(4)]
struct Buf { private int _e; }

#if BAD
[InlineArray(4)]                 // the breaking-change doc's case
record struct RBuf() { private int _e; }
#endif

class Program
{
    static void Main()
    {
        var b = new Buf();
        b[3] = 7;
        Console.WriteLine(b[3]);
    }
}
