// 슬라이드 p12-v11-sc-out — out 매개변수는 암시적으로 scoped, C# 11
using System;
using System.Diagnostics.CodeAnalysis;

class Program
{
#if BAD
    static ref int Sneaky(out int i)
    {
        i = 42;
        return ref i;                  // out is scoped now
    }
#endif
    static ref int SneakyOut([UnscopedRef] out int i)
    {
        i = 42;
        return ref i;                  // the proposal's escape hatch
    }

    // a reader-style API: out no longer pins the return value
    static Span<byte> Read(Span<byte> buffer, out int read)
    {
        read = buffer.Length / 2;
        return buffer.Slice(0, read);
    }

    static Span<byte> Use()
    {
        var buffer = new byte[256];
        int read;
        return Read(buffer, out read);
    }

    static void Main()
    {
        ref int r = ref SneakyOut(out int v);
        r++;
        Console.WriteLine(v + " " + Use().Length);
    }
}
