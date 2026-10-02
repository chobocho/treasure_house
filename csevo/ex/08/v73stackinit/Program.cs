// 슬라이드 p8-v7_3-stackallocinit — stackalloc 초기화자, C# 7.3
using System;

class App
{
    static unsafe void Main()
    {
        Span<int> a = stackalloc int[3] { 1, 2, 3 };
        Span<int> b = stackalloc int[] { 4, 5, 6 };
        ReadOnlySpan<char> v = stackalloc[] { 'a', 'e', 'i', 'o', 'u' };
        Console.WriteLine(a[2] + b[0] + " " + v.IndexOf('o'));

        int* p = stackalloc int[] { 7, 8, 9 };   // the pointer form
        Console.WriteLine(p[2]);
#if NEST
        // C# 8: stackalloc inside a larger expression
        Console.WriteLine((stackalloc int[] { 4, 2 }).IndexOf(2));
#endif
    }
}
