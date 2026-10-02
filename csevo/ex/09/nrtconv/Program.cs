// 슬라이드 p9-v8-nrt-conv — 형식 인수의 nullable 이 어긋날 때, C# 8.0
#nullable enable
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        List<string> names = new List<string> { "a" };
        IEnumerable<string?> view = names;     // out T: fine
        List<string?> alias = names;           // CS8619
        alias.Add(null);                       // the same list object
        Console.WriteLine(names.Count + " " + (names[1] == null));

        List<string?> maybe = new List<string?> { null };
        List<string> sure = maybe;             // CS8619
        Console.WriteLine(sure[0] == null);
        foreach (string? s in view) Console.Write(s ?? "null");
        Console.WriteLine();
    }
}
