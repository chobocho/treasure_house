// 슬라이드 p12-v11-utf8-static — 속성으로 둔 u8, C# 11.0
using System;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

static class Http
{
    public static ReadOnlySpan<byte> Crlf => "\r\n"u8;   // no array
    public static byte[] CrlfArray => "\r\n"u8.ToArray(); // a copy
}

class App
{
    static bool Same(ReadOnlySpan<byte> a, ReadOnlySpan<byte> b) =>
        Unsafe.AreSame(ref MemoryMarshal.GetReference(a),
                       ref MemoryMarshal.GetReference(b));

    static void Main()
    {
        Console.WriteLine("span property, same memory:  "
            + Same(Http.Crlf, Http.Crlf));
        Console.WriteLine("array property, same memory: "
            + Same(Http.CrlfArray, Http.CrlfArray));
        long before = GC.GetAllocatedBytesForCurrentThread();
        int n = 0;
        for (int i = 0; i < 100; i++) n += Http.Crlf.Length;
        long after = GC.GetAllocatedBytesForCurrentThread();
        Console.WriteLine($"{n} bytes read, allocated nothing: "
            + (after == before));
    }
}
