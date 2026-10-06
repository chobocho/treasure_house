// 슬라이드 p14-v13-orp — 오버로드 해석 우선순위, C# 13
using System;
using System.Runtime.CompilerServices;

class C1
{
#if !NOPRI
    [OverloadResolutionPriority(1)]
#endif
    public void M(ReadOnlySpan<int> s) => Console.WriteLine("Span");
    // Default overload resolution priority
    public void M(int[] a) => Console.WriteLine("Array");
}

class Program
{
    static void Main()
    {
        var d = new C1();
        int[] arr = [1, 2, 3];
        d.M(arr);          // Prints "Span"
        d.M([4, 5]);       // collection expression
    }
}
