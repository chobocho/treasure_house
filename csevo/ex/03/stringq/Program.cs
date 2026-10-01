// 슬라이드 p3-v2-nullable-ref — string? 은 C# 8 의 문법, C# 8.0
using System;

class App
{
    static void Main()
    {
        string? s = null;
        int? n = null;
        Console.WriteLine((s == null) + " " + n.HasValue);
    }
}
