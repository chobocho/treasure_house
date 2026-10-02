// 슬라이드 p10-v9-localsinit-garbage — 채우지 않은 stackalloc, C# 9.0
using System;
using System.Runtime.CompilerServices;

class App
{
    [MethodImpl(MethodImplOptions.NoInlining)]
    static int Dirty()
    {
        Span<byte> s = stackalloc byte[256];
        s.Fill(0xAB);
        return s[255];
    }

    [MethodImpl(MethodImplOptions.NoInlining)]
    static int Zeroed()
    {
        Span<byte> s = stackalloc byte[256];
        int n = 0;
        foreach (byte b in s) if (b != 0) n++;
        return n;
    }

    [SkipLocalsInit, MethodImpl(MethodImplOptions.NoInlining)]
    static int Raw()
    {
        Span<byte> s = stackalloc byte[256];
        int n = 0;
        foreach (byte b in s) if (b != 0) n++;
        return n;
    }

    static void Main()
    {
        Dirty();
        Console.WriteLine("zeroed: all zero? " + (Zeroed() == 0));
        Dirty();
        Console.WriteLine("raw   : all zero? " + (Raw() == 0));
    }
}
