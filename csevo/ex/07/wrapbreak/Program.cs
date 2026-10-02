// 슬라이드 p7-v6-wrap-break — Roslyn 이 새로 잡은 것, C# 5
using System;

class Program
{
#if BAD
    static void M<T>(T t)
    {
        lock (t) { }                // T may be a value type
    }
#endif

    static void Main()
    {
        int n = 5;
#if BAD
        if (n == null) Console.WriteLine("never");
#endif
#if BAD2
        lock (n) { }                // int is a value type
#endif
        Console.WriteLine(n);
    }
}
