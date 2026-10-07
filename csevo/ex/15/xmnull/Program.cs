// 슬라이드 p15-v14-xm-null — 수신자의 null 가능성과 특성, C# 14
using System;
using System.Diagnostics.CodeAnalysis;

static class NullExt
{
    extension(string? text)
    {
        public string OrEmpty => text ?? "";
    }

    extension([NotNullWhen(false)] string? text)
    {
        public bool IsMissing => text is null or "";
    }
}

class Program
{
    static string? Find(int key) => key > 0 ? "found" : null;

    static void Main()
    {
        string? name = Find(0);
        Console.WriteLine("[" + name.OrEmpty + "]");
        if (!name.IsMissing)
            Console.WriteLine(name.Length);   // not null here
#if WARN
        Console.WriteLine(name.Length);       // may be null here
#endif
        Console.WriteLine(name.IsMissing);
    }
}
