// 슬라이드 p14-v13-params-span — 배열과 스팬의 할당, C# 13
using System;
using System.Runtime.CompilerServices;

class Program
{
    static int sink;
    [MethodImpl(MethodImplOptions.NoInlining)]
    static void A(params int[] xs) => sink += xs.Length;
    [MethodImpl(MethodImplOptions.NoInlining)]
    static void S(params ReadOnlySpan<int> xs) => sink += xs.Length;
    static void Arr3() => A(1, 2, 3);
    static void Span3() => S(1, 2, 3);
    static void Arr0() => A();
    static void Span0() => S();
    static void ArrX(int x) => A(x, x, x, x, x, x, x, x);
    static void SpanX(int x) => S(x, x, x, x, x, x, x, x);

    static long Bytes(Action a)
    {
        a();                                    // JIT first
        long b0 = GC.GetAllocatedBytesForCurrentThread();
        for (int i = 0; i < 100; i++) a();
        return GC.GetAllocatedBytesForCurrentThread() - b0;
    }

    static void P(string label, Action a) =>
        Console.WriteLine(label + " x100: " + Bytes(a));

    static void Main()
    {
        P("params int[] (1,2,3)", Arr3);
        P("params span  (1,2,3)", Span3);
        P("params int[] ()     ", Arr0);
        P("params span  ()     ", Span0);
        P("params int[] (x * 8)", () => ArrX(sink));
        P("params span  (x * 8)", () => SpanX(sink));
    }
}
