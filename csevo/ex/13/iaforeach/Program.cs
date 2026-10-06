// 슬라이드 p13-v12-ia-foreach — foreach 와 인라인 배열, C# 12.0
using System;
using System.Runtime.CompilerServices;

[InlineArray(3)] struct Buf { int _e; }

class App
{
    static Buf field;
    static Buf Get() => field;
    static ref Buf Ref() => ref field;

    static void Main()
    {
        foreach (ref int x in field) x = 7;    // writes through
        Console.WriteLine(field[0] + field[1] + field[2]);

        foreach (var x in field)               // a span over field
        {
            field[2] = 100;
            Console.Write(x + " ");
        }
        Console.Write("| ");
        foreach (var x in Get())               // over a copy
        {
            field[2] = 5;
            Console.Write(x + " ");
        }
        Console.WriteLine();

        foreach (ref int x in Ref()) x += 1;   // ref return
        Console.WriteLine(field[0] + field[1] + field[2]);
#if BAD
        foreach (ref int x in Get()) x = 1;    // value: no ref
#endif
    }
}
