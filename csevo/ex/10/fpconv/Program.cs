// 슬라이드 p10-v9-fnptr-conv — managed 와 unmanaged 호출 규약, C# 9.0
using System;
using System.Runtime.InteropServices;

unsafe class App
{
    static int Half(int x) => x / 2;

    [UnmanagedCallersOnly]
    static int Twice(int x) => x * 2;

    static void Main()
    {
        delegate*<int, int> m = &Half;            // managed (default)
        delegate* managed<int, int> m2 = m;       // the same type
        delegate* unmanaged<int, int> u = &Twice; // platform default
        Console.WriteLine(m2(42) + " " + u(21));
#if CALL
        Console.WriteLine(Twice(1));
#endif
#if MIX
        delegate*<int, int> bad = &Twice;
        u = m;
#endif
    }
}
