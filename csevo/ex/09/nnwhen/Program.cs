// 슬라이드 p9-v8-nrt-when — MaybeNullWhen 과 Dictionary, C# 8.0
#nullable enable
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

class Store<T>
{
    readonly List<T> items = new List<T>();
    public void Add(T x) { items.Add(x); }

    // like Dictionary.TryGetValue: default(T) when false
    public bool TryFirst([MaybeNullWhen(false)] out T value)
    {
        if (items.Count > 0) { value = items[0]; return true; }
        value = default!;
        return false;
    }
}

class App
{
    static int Never(Store<string> s) =>
        s.TryFirst(out string? v) ? v.Length : v.Length;   // CS8602

    static void Main()
    {
        var s = new Store<string>();
        s.Add("abc");
        if (s.TryFirst(out string? w))
            Console.WriteLine(w.Length);      // true branch: not null
        string x;
        var d = new Dictionary<string, string>();
        x = d.TryGetValue("k", out string? y) ? y : "none";  // fine
        Console.WriteLine(x);
        string z;
        d.TryGetValue("k", out z);            // CS8600
        Console.WriteLine(z == null);
    }
}
