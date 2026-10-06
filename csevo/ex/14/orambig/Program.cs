// 슬라이드 p14-v13-or-why — 변환 둘을 가진 형식과 params, C# 13
using System;
using System.Runtime.CompilerServices;

struct Values                       // like StringValues
{
    public string[] Items;
    public static implicit operator string(Values v)
        => string.Join(",", v.Items);
    public static implicit operator string[](Values v) => v.Items;
}

static class Log
{
    public static void Write(params string[] xs)
        => Console.WriteLine("array " + xs.Length);
#if PRI
    [OverloadResolutionPriority(1)]
#endif
    public static void Write(params ReadOnlySpan<string> xs)
        => Console.WriteLine("span " + xs.Length);
}

class Program
{
    static void Main()
    {
        var v = new Values { Items = ["a", "b"] };
        Log.Write(v);
        Log.Write("x", "y", "z");
    }
}
