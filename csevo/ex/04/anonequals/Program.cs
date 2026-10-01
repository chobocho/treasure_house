// 슬라이드 p4-v3-anon-equals — Equals 는 값으로, == 는 참조로, C# 3.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        var a = new { Name = "Ann", Age = 31 };
        var b = new { Name = "Ann", Age = 31 };
        var c = new { Name = "Ann", Age = 32 };

        Console.WriteLine("a.Equals(b): " + a.Equals(b));
        Console.WriteLine("a == b:      " + (a == b));
        Console.WriteLine("a.Equals(c): " + a.Equals(c));
        Console.WriteLine("same hash:   "
            + (a.GetHashCode() == b.GetHashCode()));

        // so they work as dictionary keys (composite keys)
        Dictionary<object, string> seen =
            new Dictionary<object, string>();
        seen[a] = "first";
        seen[b] = "second";                 // same key as a
        Console.WriteLine("keys: " + seen.Count
            + ", value: " + seen[a]);
    }
}
