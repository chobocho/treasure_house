// 슬라이드 p14-v13-ri-runtime — .NET 10 의 ref struct 와, C# 13.0
using System;
using System.Collections.Generic;
using System.Linq;

class App
{
    // any enumerator, including Span<T>.Enumerator
    static int Sum<E>(E e) where E : IEnumerator<int>, allows ref struct
    {
        int s = 0;
        while (e.MoveNext()) s += e.Current;
        return s;
    }

    static void Main()
    {
        var refs = typeof(object).Assembly.GetTypes()
            .Where(t => t.IsByRefLike
                && (t.IsPublic || t.IsNestedPublic))
            .OrderBy(t => t.FullName, StringComparer.Ordinal).ToList();
        Console.WriteLine("public ref structs: " + refs.Count);
        foreach (var t in refs.Where(t => t.GetInterfaces().Length > 0))
            Console.WriteLine("  " + t.FullName + " : " + string.Join(
                ", ", t.GetInterfaces().Select(i => i.Name)));
        Console.WriteLine("Span<int> interfaces: "
            + typeof(Span<int>).GetInterfaces().Length);

        Span<int> s = stackalloc int[] { 1, 2, 3 };
        Console.WriteLine(Sum(s.GetEnumerator()));
        Console.WriteLine(Sum(new List<int> { 4, 5 }.GetEnumerator()));
    }
}
