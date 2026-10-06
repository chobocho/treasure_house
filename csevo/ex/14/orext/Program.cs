// 슬라이드 p14-v13-or-ext — 확장 메서드는 담은 정적 클래스마다, C# 13
using System;
using System.Runtime.CompilerServices;

class C2 { }

static class Ext1
{
    [OverloadResolutionPriority(1)]
    public static void M(this C2 c, Span<int> s)
        => Console.WriteLine("Ext1 Span");
    [OverloadResolutionPriority(0)]
    public static void M(this C2 c, ReadOnlySpan<int> s)
        => Console.WriteLine("Ext1 ReadOnlySpan");
}

static class Ext2
{
    [OverloadResolutionPriority(0)]
    public static void M(this C2 c, ReadOnlySpan<int> s)
        => Console.WriteLine("Ext2 ReadOnlySpan");
}

class Program
{
    static void Main()
    {
        new C2().M([1, 2, 3]);     // Will print Ext2 ReadOnlySpan
        Ext1.M(new C2(), [1, 2, 3]);
    }
}
