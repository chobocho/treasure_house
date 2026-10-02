// 슬라이드 p9-v8-nrt-tq — 제약 없는 T? 는 C# 9, C# 9.0
#nullable enable
using System;
using System.Collections.Generic;

class App
{
    static T? FirstOrNone<T>(List<T> xs) =>
        xs.Count == 0 ? default : xs[0];

    static void Main()
    {
        string? s = FirstOrNone(new List<string>());
        int i = FirstOrNone(new List<int>());     // T? of int is int
        Console.WriteLine((s ?? "null") + " " + i);
    }
}
