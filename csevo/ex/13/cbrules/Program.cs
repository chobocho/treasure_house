// 슬라이드 p13-v12-cb-rules — 빌더 메서드의 규칙, C# 12
using System;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.CompilerServices;

#if BAD
[CollectionBuilder(typeof(Builder), "Make")]
#elif BAD2
[CollectionBuilder(typeof(Builder), "Arr")]
#else
[CollectionBuilder(typeof(Builder), "Create")]
#endif
class Pair : IEnumerable<int>
{
    public int[] Items = [];
    public IEnumerator<int> GetEnumerator() =>
        ((IEnumerable<int>)Items).GetEnumerator();
    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
}

static class Builder
{
    public static Pair Create(ReadOnlySpan<int> s) =>
        new Pair { Items = s.ToArray() };
    public static Pair Arr(int[] a) => new Pair { Items = a };
}

class Program
{
    static void Main()
    {
        Pair p = [1, 2];
        Console.WriteLine(p.Items.Length);
    }
}
