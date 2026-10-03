// 슬라이드 p12-v11-lp-types — 목록 패턴을 받는 형식, C# 11
using System;
using System.Collections.Generic;

class Bag   // countable + indexable, not sliceable
{
    readonly int[] items;
    public Bag(params int[] items) { this.items = items; }
    public int Count => items.Length;
    public int this[int i] => items[i];
}

class Program
{
    static void Main()
    {
        var b = new Bag(1, 2, 3);
        Console.WriteLine(b is [1, _, 3]);
        Console.WriteLine(b is [.., 3]);     // ^1 -> Count - 1
        Console.WriteLine(b is [1, ..]);     // bare .. is fine
#if BAD
        Console.WriteLine(b is [1, .. var r]);   // no slicer
#endif
#if BAD2
        IEnumerable<int> seq = new[] { 1, 2, 3 };
        Console.WriteLine(seq is [1, ..]);   // not countable
#endif
    }
}
