// 슬라이드 p13-v12-ia-not — 인라인 배열이 아직 못 하는 것, C# 12.0
using System;
using System.Runtime.CompilerServices;

[InlineArray(4)] struct Buf { int _e; }
class Box { public Buf F; }

class App
{
    static void Main()
    {
        var b = new Buf();
        b[0] = 1;
        int[] all = [.. b, 9];     // spread: ok
        Console.WriteLine(string.Join(",", all));
        var box = new Box();
        box.F[3] = 4;              // through a field: ok
        Console.WriteLine(box.F[3]);
#if BAD
        Buf c = [1, 2, 3, 4];      // as a collection target
#elif BAD2
        if (b is [1, ..]) { }      // list pattern
#elif BAD3
        var d = new Box { F = { [0] = 1 } };   // initializer
#elif BAD4
        int n = b.Length;          // no Length member
#endif
    }
}
