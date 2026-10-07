// 슬라이드 p15-v14-xm-orp — 확장 블록과 오버로드 해석 우선순위, C# 14
using System;
using System.Runtime.CompilerServices;

static class Ext
{
    extension(int[] a)
    {
        public string Describe() => "array";
    }

    extension(ReadOnlySpan<int> s)
    {
#if !NOORP
        [OverloadResolutionPriority(1)]
#endif
        public string Describe() => "span";
    }
}

class Program
{
    static void Main()
    {
        int[] xs = { 1, 2 };
        Console.WriteLine(xs.Describe());            // priority 1 wins
        Console.WriteLine(Ext.Describe(xs));         // static form too
        Console.WriteLine(new ReadOnlySpan<int>(xs).Describe());
    }
}
