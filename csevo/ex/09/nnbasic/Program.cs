// 슬라이드 p9-v8-notnull — notnull 제약, C# 8.0
using System;
using System.Collections.Generic;

// a key may be a struct or a class, but never null
class Registry<TKey> where TKey : notnull
{
    readonly List<TKey> keys = new List<TKey>();
    public void Add(TKey key) { keys.Add(key); }
    public int Count { get { return keys.Count; } }
}

class App
{
    static void Main()
    {
        var r = new Registry<string>();
        r.Add("a");
        var n = new Registry<int>();
        n.Add(1);
        n.Add(2);
        Console.WriteLine(r.Count + " " + n.Count);
    }
}
