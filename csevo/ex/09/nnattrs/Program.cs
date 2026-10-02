// 슬라이드 p9-v8-nrt-attrs — 시그니처로 말할 수 없는 null 규칙, C# 8.0
#nullable enable
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

class Cache
{
    readonly Dictionary<int, string> map =
        new Dictionary<int, string> { { 1, "one" } };

    // value is null exactly when the method returns false
    public bool TryGet(int key, [NotNullWhen(true)] out string? value)
    {
        if (map.TryGetValue(key, out string? v))
        {
            value = v;
            return true;
        }
        value = null;
        return false;
    }
}

class App
{
    static void Main()
    {
        var c = new Cache();
        if (c.TryGet(1, out string? s))
            Console.WriteLine(s.Length);      // no warning: true branch
        if (!c.TryGet(2, out string? t))
            Console.WriteLine(t == null);
    }
}
