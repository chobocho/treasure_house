// 슬라이드 p9-v8-nrt-classq — class 와 class? 제약, C# 8.0
#nullable enable
using System;

class C
{
    static string A<T>(T t) where T : class => t.ToString()!;
    static string B<T>(T t) where T : class? => t?.ToString() ?? "null";

    static void Main()
    {
        Console.WriteLine(A<string>("a"));
        Console.WriteLine(A<string?>("a?"));     // CS8634
        Console.WriteLine(B<string?>(null));     // fine
    }
}
