// 슬라이드 p9-v8-nestedstackalloc — 식 안의 stackalloc, C# 8.0
using System;

class App
{
    static int Sum(ReadOnlySpan<int> xs)
    {
        int s = 0;
        foreach (int x in xs) s += x;
        return s;
    }

    static void Main()
    {
        Span<int> numbers = stackalloc[] { 1, 2, 3, 4, 5, 6 };
        var ind = numbers.IndexOfAny(stackalloc[] { 2, 4, 6, 8 });
        Console.WriteLine(ind);                       // 1

        Console.WriteLine(Sum(stackalloc[] { 10, 20, 30 }));

        int n = 4;                    // small: stack, large: heap
        Span<int> buf = n <= 64 ? stackalloc int[n] : new int[n];
        Console.WriteLine(buf.Length);
    }
}
