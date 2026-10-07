// 슬라이드 p15-v14-xm-ienum — whats-new 의 IsEmpty·Identity, C# 14
using System;
using System.Collections.Generic;
using System.Linq;

static class SeqExt
{
    extension<TSource>(IEnumerable<TSource> source)
    {
        public bool IsEmpty => !source.Any();
    }

    extension<TSource>(IEnumerable<TSource>)
    {
        public static IEnumerable<TSource> Identity =>
            Enumerable.Empty<TSource>();
        public static IEnumerable<TSource> operator +(
            IEnumerable<TSource> left, IEnumerable<TSource> right)
            => left.Concat(right);
    }
}

class Program
{
    static void Main()
    {
        int[] data = { 1, 2, 3 };
        IEnumerable<int> seq = data;
        Console.WriteLine(data.IsEmpty + " " + new List<int>().IsEmpty);
        Console.WriteLine(IEnumerable<int>.Identity.IsEmpty);
        var combined = seq + new[] { 4, 5 };
        Console.WriteLine(string.Join(",", combined));
        var c2 = data + new[] { 6 };       // int[] + int[]
        var c3 = data + [4, 5];            // the blog's usage
        Console.WriteLine(string.Join(",", c2) + " " + c3.Count());
    }
}
