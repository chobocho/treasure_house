// 슬라이드 p15-v14-sp-ros — ReadOnlySpan 판이 이겨서 깨지는 코드, C# 14
using System;
using System.Runtime.InteropServices;

class Program
{
    static string Kind<T>(T value) where T : allows ref struct
        => typeof(T).Name;

    static void Main()
    {
        double[] x = [1.0, -2.0];
#if OLD
        Span<ulong> y = MemoryMarshal.Cast<double, ulong>(x);  // C# 13
#endif
        Span<ulong> z = MemoryMarshal.Cast<double, ulong>(x.AsSpan());
        Console.WriteLine(z[0].ToString("X16"));
        Console.WriteLine(Kind(MemoryMarshal.Cast<double, ulong>(x)));
    }
}
