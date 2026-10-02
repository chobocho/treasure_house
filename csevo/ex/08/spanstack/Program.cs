// 슬라이드 p8-v7_2-stackalloc — unsafe 없는 stackalloc, C# 7.2
using System;

class App
{
    static int SumOfSquares(int n)
    {
        Span<int> buf = stackalloc int[n];   // on the stack, no unsafe
        for (int i = 0; i < buf.Length; i++) buf[i] = i * i;
        int s = 0;
        foreach (int x in buf) s += x;
        return s;
    }

    static void Main()
    {
        Console.WriteLine(SumOfSquares(4));
        Span<byte> b = stackalloc byte[3];
        Console.WriteLine(b[0] + b[1] + b[2]);   // zeroed
        try { b[3] = 1; }                        // bounds checked
        catch (IndexOutOfRangeException e)
        {
            Console.WriteLine(e.GetType().Name);
        }
#if BAD
        int* p = stackalloc int[3];              // a pointer: unsafe
#endif
    }
}
