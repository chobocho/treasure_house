// 슬라이드 p13-v12-collbuilder — 내 형식에 [CollectionBuilder], C# 12
using System;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.CompilerServices;

[CollectionBuilder(typeof(BagBuilder), "Create")]
class Bag<T> : IEnumerable<T>
{
    readonly T[] items;
    public Bag(T[] items) { this.items = items; }
    public IEnumerator<T> GetEnumerator() =>
        ((IEnumerable<T>)items).GetEnumerator();
    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
}

static class BagBuilder
{
    public static Bag<T> Create<T>(ReadOnlySpan<T> span)
    {
        Console.WriteLine("Create(" + span.Length + ")");
        return new Bag<T>(span.ToArray());
    }
}

class Program
{
    static void Main()
    {
        Bag<int> a = [1, 2, 3];
        int[] more = [4, 5];
        Bag<int> b = [.. a, .. more];
        Bag<string> e = [];
        Console.WriteLine(string.Join(",", b) + " " + e.GetType().Name);
    }
}
