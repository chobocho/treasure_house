// 슬라이드 p14-v13-ar-func — Func 와 Action 이 Span 을 받는다, C# 13.0
using System;

class App
{
    static void Main()
    {
        // .NET 10's Func<T, TResult> allows ref struct type arguments
        Func<ReadOnlySpan<char>, int> count = s => s.Count('a');
        Console.WriteLine(count("banana"));

        Action<Span<int>> fill = s => s.Fill(7);
        Span<int> buf = stackalloc int[3];
        fill(buf);
        Console.WriteLine(buf[0] + buf[1] + buf[2]);

        // the natural type of a lambda with a Span parameter
        var len = (Span<int> s) => s.Length;
        Console.WriteLine(len.GetType());
        Console.WriteLine(len(buf));
    }
}
