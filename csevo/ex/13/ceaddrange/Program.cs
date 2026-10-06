// 슬라이드 p13-v12-ce-addrange — 펼침은 Add 를 몇 번 부르나, C# 12
using System;
using System.Collections;
using System.Collections.Generic;

class Box : IEnumerable<int>
{
    readonly List<int> items = [];
    public void Add(int x)
    {
        Console.Write("Add(" + x + ") ");
        items.Add(x);
    }
    public void AddRange(IEnumerable<int> xs)
    {
        Console.Write("AddRange ");
        items.AddRange(xs);
    }
    public IEnumerator<int> GetEnumerator() => items.GetEnumerator();
    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
}

class Program
{
    static void Main()
    {
        int[] xs = [1, 2];
        Box b = [0, .. xs];
        Console.WriteLine();
        List<int> big = [.. xs, .. xs];   // List<T>: no Add per item?
        Console.WriteLine(big.Count);
    }
}
