// 슬라이드 p9-v8-nrt-struct — default 와 구조체 필드, C# 8.0
#nullable enable
using System;

struct Pair
{
    public string Key;
    public Pair(string key) { Key = key; }
}

class App
{
    static void Never()
    {
        string s = default;                // CS8600
        Pair p = default;                  // no warning here...
        Pair q = new Pair();
        Console.WriteLine(s + p.Key.Length + q.Key.Length);  // ...here
    }

    static void Main()
    {
        Pair[] r = new Pair[1];            // no warning
        Console.WriteLine(r[0].Key == null);
        Console.WriteLine(r[0].Key.Length);   // no warning
    }
}
