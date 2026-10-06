// 슬라이드 p13-v12-rr-old — C# 11 에서 부르는 ref readonly, C# 11.0
using System;
using System.Runtime.CompilerServices;

class App
{
    static void Main()
    {
        int x = 3;
        // both parameters are 'ref readonly' in .NET 10
        Console.WriteLine(Unsafe.IsNullRef(ref x));
        var s = new ReadOnlySpan<int>(ref x);
#if BAD
        var t = new ReadOnlySpan<int>(in x);
#elif BAD2
        var t = new ReadOnlySpan<int>(x);
#endif
        Console.WriteLine(s[0] + " " + s.Length);
    }
}
