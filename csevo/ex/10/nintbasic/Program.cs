// 슬라이드 p10-v9-nint — 원시 크기 정수 nint·nuint, C# 9.0
using System;

class App
{
    static unsafe void Main()
    {
        nint a = 40;
        nuint b = 2;
        nint c = a + (nint)b;
        Console.WriteLine($"c = {c}, sizeof(nint) = {sizeof(nint)}");
        Console.WriteLine("nint.MaxValue  = " + nint.MaxValue);
        Console.WriteLine("nuint.MaxValue = " + nuint.MaxValue);
        Console.WriteLine("IntPtr.Size    = " + IntPtr.Size);
    }
}
