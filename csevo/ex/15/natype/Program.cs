// 슬라이드 p15-v14-na-type — 대입식의 값과 형식, C# 14
using System;

class Box
{
    public int N;
    public string S;
}

class Holder<T>
{
    public T Value;
}

class Program
{
    static string Kind<T>(T x) =>
        typeof(T).Name + "=" + (x?.ToString() ?? "null");

    static void Set<T>(Holder<T> h, T t)
    {
        h?.Value = t;                       // a statement: fine
#if GENERIC
        Console.WriteLine((h?.Value = t).ToString());
#endif
    }

    static void Main()
    {
        Box b = new Box(), none = null;
        Console.WriteLine(Kind(b?.N = 5));       // int?
        Console.WriteLine(Kind(none?.N = 5));
        Console.WriteLine(Kind(b?.S = "s"));     // string
        int? r = none?.N += 1;
        Console.WriteLine(r.HasValue);
        Set(new Holder<int>(), 1);
    }
}
