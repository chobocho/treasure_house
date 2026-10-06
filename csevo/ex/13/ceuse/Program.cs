// 슬라이드 p13-v12-ce-use — foreach · 인수 · 반환 · 기본값, C# 12
using System;
using System.Collections.Generic;

class Program
{
    static int Sum(IEnumerable<int> xs)
    {
        int s = 0;
        foreach (int x in xs) s += x;
        return s;
    }

    static int[] Pick(bool all) => all ? [1, 2, 3] : [1];
#if BAD2
    static int Count(int[] xs = []) => xs.Length;
#endif

    static void Main()
    {
        Console.WriteLine(Sum([1, 2, 3]) + " " + Pick(false).Length);
        foreach (int x in (int[])[4, 5])
            Console.Write(x + " ");
        Console.WriteLine();
#if BAD
        foreach (int x in [4, 5])
            Console.Write(x);
#endif
    }
}
