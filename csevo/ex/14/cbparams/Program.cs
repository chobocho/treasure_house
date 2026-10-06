// 슬라이드 p14-v13-pm-builder — 빌더 형식을 params 로, C# 13
using System;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.CompilerServices;

[CollectionBuilder(typeof(Bag), nameof(Bag.Create))]
class Bag<T> : IEnumerable<T>
{
    readonly T[] items;
    public Bag(T[] items) => this.items = items;
    public int Count => items.Length;
    public IEnumerator<T> GetEnumerator() =>
        ((IEnumerable<T>)items).GetEnumerator();
    IEnumerator IEnumerable.GetEnumerator() => items.GetEnumerator();
}

static class Bag
{
    public static Bag<T> Create<T>(ReadOnlySpan<T> xs)
    {
        Console.Write("Create(" + xs.Length + ") ");
        return new Bag<T>(xs.ToArray());
    }
}

class Program
{
    static int Count(params Bag<string> b) => b.Count;

    static void Main()
    {
        Console.WriteLine(Count("x", "y", "z"));
        Console.WriteLine(Count());
        Console.WriteLine(Count(["w"]));
    }
}
