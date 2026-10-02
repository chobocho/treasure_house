// 슬라이드 p9-v8-nrt-why — nullable 이전의 null, C# 7.3
using System;
using System.Collections.Generic;

class App
{
    static readonly Dictionary<int, string> names =
        new Dictionary<int, string> { { 1, "Ada" } };

    // Nothing in the signature says that null can come back.
    static string Find(int id)
    {
        return names.TryGetValue(id, out string n) ? n : null;
    }

    static void Main()
    {
        Console.WriteLine(Find(1).Length);
        Console.WriteLine(Find(2).Length);   // compiles cleanly
    }
}
