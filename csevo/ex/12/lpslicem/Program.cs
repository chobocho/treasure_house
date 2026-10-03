// 슬라이드 p12-v11-lp-slicem — Slice(int, int) 로 자르는 형식, C# 11
using System;

class Bag
{
    readonly int[] items;
    public Bag(params int[] items) { this.items = items; }
    public int Count => items.Length;
    public int this[int i] => items[i];
    public Bag Slice(int start, int length)
    {
        Console.WriteLine("  Slice({0}, {1})", start, length);
        return new Bag(items.AsSpan(start, length).ToArray());
    }
    public override string ToString() =>
        "Bag(" + string.Join(",", items) + ")";
}

class Program
{
    static void Main()
    {
        var b = new Bag(1, 2, 3, 4, 5);
        if (b is [_, .. var mid, _])
            Console.WriteLine("mid = {0}", mid);
        if (b is [.. var all])
            Console.WriteLine("all = {0}", all);
        if (b is [var f, .. var rest])
            Console.WriteLine("f = {0}, rest = {1}", f, rest);
        if (b is [1, .. [var x, ..], 5])
            Console.WriteLine("x = {0}", x);
        Console.WriteLine(b is [1, .., 5]);   // no Slice call
    }
}
