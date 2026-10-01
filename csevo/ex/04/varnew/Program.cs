// 슬라이드 p4-v3-var-later — 반대 방향의 생략: 대상 형식 new(), C# 9
using System;
using System.Collections.Generic;

class App
{
    static readonly Dictionary<string, List<int>> cache = new();

    static void Main()
    {
        var a = new List<int>();      // C# 3: type on the right
        List<int> b = new();          // C# 9: type on the left
        a.Add(1);
        b.Add(2);
        cache["k"] = b;
        Console.WriteLine(a.Count + b.Count + cache.Count);
    }
}
