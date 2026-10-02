// 슬라이드 p9-v8-nested-ptr — 문맥이 정하는 stackalloc 의 형식, C# 8.0
using System;

class App
{
    static void Main()
    {
        Span<int> a = stackalloc int[2];      // target Span<int>: safe
        var b = stackalloc int[2];            // a declaration: int*
        Console.WriteLine(a.Length);
    }
}
