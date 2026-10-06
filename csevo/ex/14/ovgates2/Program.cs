// 슬라이드 p14-v13-gates-demo2 — 선언의 C# 13 기능 다섯, C# 13
using System;
using System.Runtime.CompilerServices;

interface IName { string Name { get; } }

ref struct Tag : IName                    // ref struct interface
{
    public string Name => "tag";
}

partial class Person
{
    public partial string First { get; }   // partial property
}
partial class Person
{
    public partial string First => "Ada";
}

class Program
{
    static int Sum(params ReadOnlySpan<int> xs)   // params collection
    {
        int s = 0;
        foreach (int x in xs) s += x;
        return s;
    }

    static string Show<T>(T x) where T : IName, allows ref struct
        => x.Name;                         // allows ref struct

    [OverloadResolutionPriority(1)]        // overload priority
    static string Pick(object o) => "object";
    static string Pick(string s) => "string";

    static void Main()
    {
        Console.WriteLine(Sum(1, 2, 3) + " " + new Person().First);
        Console.WriteLine(Show(new Tag()) + " " + Pick("x"));
    }
}
