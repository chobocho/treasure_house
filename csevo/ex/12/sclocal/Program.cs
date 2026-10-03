// 슬라이드 p12-v11-sc-local — scoped 지역 변수, C# 11
using System;

class Program
{
    static int Sum(int n)
    {
        // scoped: may hold heap memory or stack memory later
        scoped Span<int> buf = n > 8 ? new int[n] : default;
        if (n <= 8) buf = stackalloc int[n];
        for (int i = 0; i < n; i++) buf[i] = i + 1;
        int s = 0;
        foreach (int v in buf) s += v;
        return s;
    }

    static Span<int> Bad()
    {
#if BAD
        scoped Span<int> span = default;
        return span;                      // scoped wins
#else
        Span<int> span2 = default;        // caller-context
#if BAD2
        span2 = stackalloc int[4];
#endif
        return span2;
#endif
    }

    static void Main()
    {
        Console.WriteLine(Sum(4) + " " + Sum(100));
        Console.WriteLine(Bad().Length);
    }
}
