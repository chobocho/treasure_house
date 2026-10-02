// 슬라이드 p9-v8-range-copy — 배열은 복사, Span 은 공유, C# 8.0
using System;

class App
{
    static void Main()
    {
        int[] a = { 1, 2, 3, 4, 5 };

        int[] copy = a[1..3];            // RuntimeHelpers.GetSubArray
        copy[0] = 99;
        Console.WriteLine("after copy[0]=99:  " + string.Join(",", a));

        Span<int> view = a.AsSpan()[1..3];   // Span<int>.Slice
        view[0] = 99;
        Console.WriteLine("after view[0]=99:  " + string.Join(",", a));

        // even the whole range is a new array
        Console.WriteLine("a[..] is a: {0}", ReferenceEquals(a[..], a));
    }
}
