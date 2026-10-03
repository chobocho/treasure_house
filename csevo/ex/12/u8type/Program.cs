// 슬라이드 p12-v11-utf8-type — u8 의 형식은 ReadOnlySpan<byte>, C# 11.0
using System;

class App
{
    static string Kind(ReadOnlySpan<byte> _) => "ReadOnlySpan<byte>";
    static string Kind(byte[] _) => "byte[]";

    static void Main()
    {
        var a = "ok"u8;
        var b = "OK"U8;                   // suffix is case-insensitive
        byte[] c = "ok"u8.ToArray();            // a copy on the heap
        Console.WriteLine(Kind(a) + " " + Kind(b) + " " + Kind(c));
#if STR
        string s = "ok"u8;
#endif
#if ARR
        byte[] arr = "ok"u8;
#endif
#if SPAN
        Span<byte> span = "ok"u8;
#endif
#if NOSUFFIX
        ReadOnlySpan<byte> plain = "ok";
#endif
#if BOX
        object o = "ok"u8;
#endif
#if CONST
        const ReadOnlySpan<byte> k = "ok"u8;
#endif
    }
#if DEFAULT
    static void Write(ReadOnlySpan<byte> m = "missing"u8) { }
#endif
}
