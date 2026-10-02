// 슬라이드 p8-v7_2-span — 같이 온 런타임: Span 가족, C# 7.2
using System;

class App
{
    static void Show(Type t)
    {
        Console.WriteLine(t.Name.PadRight(22)
            + " ref-like=" + t.IsByRefLike.ToString().PadRight(5)
            + " @ " + t.Assembly.GetName().Name);
    }

    static void Main()
    {
        Show(typeof(Span<>));
        Show(typeof(ReadOnlySpan<>));
        Show(typeof(Memory<>));
        Show(typeof(ReadOnlyMemory<>));
        Show(typeof(MemoryExtensions));
        Show(typeof(TypedReference));
        Show(typeof(ArgIterator));
        Show(typeof(RuntimeArgumentHandle));
    }
}
