// 슬라이드 p13-v12-ce-later — 뒤 버전: params 컬렉션, C# 13
using System;
using System.Collections.Generic;

class Program
{
    static int Sum(params ReadOnlySpan<int> xs)
    {
        int s = 0;
        foreach (int x in xs) s += x;
        return s;
    }

    static int Count(params IEnumerable<int> xs) =>
        xs is ICollection<int> c ? c.Count : -1;

    static void Main()
    {
        int[] a = [1, 2];
        Console.WriteLine(Sum(1, 2, 3) + " " + Sum([.. a, 3]) + " "
                          + Sum());
        Console.WriteLine(Count(4, 5) + " " + Count([.. a, .. a]));
    }
}
