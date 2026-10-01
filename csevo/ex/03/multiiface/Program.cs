// 슬라이드 p3-v2-generic-interface — 제네릭 인터페이스 두 번, C# 2.0
using System;

interface IParser<T>
{
    T Parse(string s);
}

class Both : IParser<int>, IParser<bool>
{
    int IParser<int>.Parse(string s) { return int.Parse(s); }
    bool IParser<bool>.Parse(string s) { return s == "yes"; }
}

class App
{
    static T Read<T>(IParser<T> p, string s)
    {
        return p.Parse(s);
    }

    static void Main()
    {
        Both b = new Both();
        Console.WriteLine(Read<int>(b, "42") + 1);
        Console.WriteLine(Read<bool>(b, "yes"));
        Console.WriteLine(b is IParser<int>);
        Console.WriteLine(b is IParser<string>);
        Console.WriteLine(typeof(Both).GetInterfaces().Length);
    }
}
