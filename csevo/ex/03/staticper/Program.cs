// 슬라이드 p3-v2-static-per-type — 닫힌 형식마다 정적 필드, C# 2.0
using System;

class Counter<T>
{
    public static int Count;

    static Counter()
    {
        Console.WriteLine("static ctor for " + typeof(T).Name);
    }

    public Counter()
    {
        Count++;
    }
}

class App
{
    static void Main()
    {
        new Counter<int>();
        new Counter<int>();
        new Counter<string>();
        Console.WriteLine(Counter<int>.Count);
        Console.WriteLine(Counter<string>.Count);
        Console.WriteLine(Counter<double>.Count);
    }
}
