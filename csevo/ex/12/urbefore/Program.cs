// 슬라이드 p12-v11-ur-before — 캐스트 두 번에서 >>> 로, C# 11.0
using System;

class App
{
    static void Main()
    {
        int n = -8;
        // Before C# 11: to uint, shift, back to int
        int old = (int)((uint)n >> 1);
        Console.WriteLine(old + " " + (n >>> 1) + " "
            + (old == n >>> 1));

        // Small types are promoted to int first
        sbyte sb = -8;
        var r = sb >>> 1;
        Console.WriteLine(r + " " + r.GetType().Name);
        Console.WriteLine((sbyte)((byte)sb >> 1));   // the 8-bit answer

        // The count is masked: & 31 for int, & 63 for long
        Console.WriteLine((1 >>> 33) + " " + (1 << 33) + " "
            + (1L << 33));
    }
}
