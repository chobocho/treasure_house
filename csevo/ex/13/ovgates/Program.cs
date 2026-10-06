// 슬라이드 p13-v12-gates-demo — 몸체 안의 C# 12 기능 여섯, C# 12.0
using System;
using System.Runtime.CompilerServices;

[InlineArray(3)]
struct Buf { int e; }

class App
{
    string Name = "app";

    static void Main()
    {
        int[] xs = [1, 2, 3];                       // collection expr
        var inc = (int v, int by = 1) => v + by;    // lambda default
        var cnt = (params int[] vs) => vs.Length;   // lambda params
        string n = nameof(Name.Length);             // nameof instance
        var b = new Buf();
        b[0] = 7;                                   // inline array
        int k = 5;
        Console.WriteLine($"{xs.Length} {inc(1)} {cnt(1, 2)} {n}");
        Console.WriteLine($"{b[0]} {Peek(ref k)}");

        static int Peek(ref readonly int r) => r;   // ref readonly
    }
}
