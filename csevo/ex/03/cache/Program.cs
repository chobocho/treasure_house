// 슬라이드 p3-v2-generic-cache — 형식마다 한 번만 계산하기, C# 2.0
using System;

class TypeInfoCache<T>
{
    public static readonly string Text = Compute();

    static TypeInfoCache() { }            // run exactly on first use

    static string Compute()
    {
        Console.WriteLine("  computing for " + typeof(T).Name);
        string kind = typeof(T).IsValueType ? " (value)" : "";
        return typeof(T).FullName + kind;
    }
}

class App
{
    static void Main()
    {
        Console.WriteLine(TypeInfoCache<int>.Text);
        Console.WriteLine(TypeInfoCache<int>.Text);
        Console.WriteLine(TypeInfoCache<string>.Text);
    }
}
