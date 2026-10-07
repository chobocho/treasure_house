// 슬라이드 p15-v14-sp-cov — ReadOnlySpan 의 공변, C# 14
using System;

class Program
{
    static string Join(ReadOnlySpan<object> items)
    {
        string s = "";
        foreach (object o in items) s += o + ";";
        return s;
    }

    static void Main()
    {
        string[] words = ["a", "b"];
        Span<string> sw = words;
        ReadOnlySpan<string> rw = words;
        Console.WriteLine(Join(words));      // string[]
        Console.WriteLine(Join(sw));         // Span<string>
        Console.WriteLine(Join(rw));         // ReadOnlySpan<string>
        ReadOnlySpan<object> ro = rw;
        Console.WriteLine(ro[0].GetType().Name);
    }
}
