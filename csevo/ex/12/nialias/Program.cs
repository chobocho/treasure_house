// 슬라이드 p12-v11-nint — nint 는 System.IntPtr 의 별칭, C# 11.0
using System;
using System.Runtime.CompilerServices;

class App
{
    const nint K = 5;

    static void Main()
    {
        Console.WriteLine(RuntimeFeature.IsSupported(
            nameof(RuntimeFeature.NumericIntPtr)));
        Console.WriteLine(typeof(nint) == typeof(IntPtr));
        nint n = K;
        IntPtr p = n * 2 + 1;                   // IntPtr arithmetic
        Console.WriteLine(p + " " + p.GetType().FullName);
        // C# 9's spec hid these members from nint
        Console.WriteLine(nint.Zero + " " + nint.Size + " "
            + nint.Parse("42"));
    }
}
