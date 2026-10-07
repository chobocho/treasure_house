// 슬라이드 p15-v14-lm-ref — ref·in·scoped 와 ref struct, C# 14
using System;

delegate void Bump(ref int x);
delegate int Peek(in int x);
delegate int Look(ref readonly int x);
delegate ReadOnlySpan<int> Head(scoped ReadOnlySpan<int> s);

class Program
{
    static readonly int[] Seven = [7];

    static void Main()
    {
        Bump bump = (ref x) => x++;
        Peek peek = (in x) => x * 10;
        Look look = (ref readonly x) => x + 100;
        Head head = (scoped s) => s.IsEmpty ? default : Seven;
        int n = 1;
        bump(ref n);
        Console.WriteLine(n + " " + peek(n) + " " + look(ref n) + " "
            + head([1, 2])[0]);
#if NOSCOPED
        Head bad = (s) => Seven;
#endif
    }
}
