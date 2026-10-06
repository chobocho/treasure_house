// 슬라이드 p14-v13-pm-concrete — 구체 형식의 params, C# 13
using System;
using System.Collections.Generic;
using System.Collections.Immutable;

class Program
{
    static string Lst(params List<int> xs) =>
        xs.GetType().Name + " Count=" + xs.Count
        + " Capacity=" + xs.Capacity;
    static string Set(params HashSet<int> xs) =>
        xs.GetType().Name + " Count=" + xs.Count;
    static string Imm(params ImmutableArray<int> xs) =>
        xs.GetType().Name + " Length=" + xs.Length;
    static string Spn(params Span<int> xs)
    {
        xs[0] = 99;                     // Span<T> is writable
        return "Span`1 Length=" + xs.Length + " [0]=" + xs[0];
    }

    static void Main()
    {
        Console.WriteLine(Lst(1, 2, 3));
        Console.WriteLine(Set(1, 2, 2, 3));   // duplicates collapse
        Console.WriteLine(Imm(1, 2, 3));
        Console.WriteLine(Spn(1, 2, 3));
        Console.WriteLine(Lst());
    }
}
