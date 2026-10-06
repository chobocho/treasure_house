// 슬라이드 p13-v12-ia-rules — [InlineArray] 의 규칙, C# 12.0
using System;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

[InlineArray(2)]
struct Ok
{
    static int Count;              // static fields do not count
    int _e;
    public static int Next() => ++Count;
}
#if R1
[InlineArray(4)] struct Two { int a; int b; }
#elif R2
[InlineArray(0)] struct Zero { int a; }
#elif R3
[InlineArray(4)]
[StructLayout(LayoutKind.Explicit)]
struct Ex { [FieldOffset(0)] int a; }
#elif R4
[InlineArray(4)] record struct Rec { int a; }
#elif R5
[InlineArray(4)] class Cls { int a; }
#endif

class App
{
    static void Main()
    {
        var o = new Ok();
        o[1] = Ok.Next();
        Console.WriteLine(o[0] + " " + o[1]);
    }
}
