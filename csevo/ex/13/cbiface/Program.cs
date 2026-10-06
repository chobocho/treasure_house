// 슬라이드 p13-v12-cb-iface — 인터페이스의 빌더, C# 12
using System;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.CompilerServices;

[CollectionBuilder(typeof(Seq), "Of")]
interface ISeq<T> : IEnumerable<T>
{
    int Count { get; }
}

static class Seq
{
    public static ISeq<T> Of<T>(ReadOnlySpan<T> s) =>
        new ArraySeq<T>(s);

    sealed class ArraySeq<T>(ReadOnlySpan<T> s) : ISeq<T>
    {
        readonly T[] items = s.ToArray();
        public int Count => items.Length;
        public IEnumerator<T> GetEnumerator() =>
            ((IEnumerable<T>)items).GetEnumerator();
        IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
    }
}

class Program
{
    static int Total(ISeq<int> xs) => System.Linq.Enumerable.Sum(xs);

    static void Main()
    {
        ISeq<int> s = [1, 2, 3];
        Console.WriteLine(s.Count + " " + Total([4, 5]) + " "
                          + s.GetType().Name);
    }
}
