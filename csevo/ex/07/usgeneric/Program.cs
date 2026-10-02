// 슬라이드 p7-v6-us-generic — 닫힌 제네릭 형식을 using static, C# 6.0
using System;
using static Counter<int>;

static class Counter<T>
{
    public static int Hits;
    public static string Name() { return typeof(T).Name; }
}

class Program
{
    static void Main()
    {
        Hits++;
        Hits++;
        Console.WriteLine(Name() + " " + Hits);
        Console.WriteLine("string: " + Counter<string>.Hits);
    }
}
