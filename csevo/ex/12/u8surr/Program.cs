// 슬라이드 p12-v11-utf8-surrogate — 짝이 안 맞는 서로게이트, C# 11.0
using System;
using System.Text;

class App
{
    static void Dump(ReadOnlySpan<byte> bytes)
    {
        foreach (byte b in bytes)
            Console.Write(b.ToString("X2") + " ");
        Console.WriteLine();
    }

    static void Main()
    {
        Dump("😀"u8);              // a valid surrogate pair
        Dump(Encoding.UTF8.GetBytes("\uD801"));  // runtime: U+FFFD
#if LONE
        Dump("\uD801"u8);                    // a lone high surrogate
#endif
#if TWOHIGH
        Dump("hello \uD801\uD802"u8);        // the proposal's example
#endif
    }
}
