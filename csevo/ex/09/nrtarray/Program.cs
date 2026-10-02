// 슬라이드 p9-v8-nrt-array — 배열 원소는 따라가지 못한다, C# 8.0
#nullable enable
using System;

class App
{
    static void Main()
    {
        string[] a = new string[3];        // three nulls, no warning
        string?[] b = new string?[3];      // elements may be null
        string[]? c = null;                // the array may be null
        Console.WriteLine(b[0]?.Length ?? -1);
        Console.WriteLine(c?.Length ?? -1);
        Console.WriteLine(a[0] == null);
        Console.WriteLine(a[0].Length);    // no warning
    }
}
