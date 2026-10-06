// 슬라이드 p14-v13-mgnatural — 메서드 그룹 자연 형식의 개선, C# 13
using System;

class C
{
    public void M(int x) => Console.WriteLine("C.M(int)");
}

static class E
{
    public static void M(this C c, string s)
        => Console.WriteLine("E.M(string)");
}

class Program
{
    static void Main()
    {
        var f = new C().M;       // instance scope first
        f(1);
        Console.WriteLine(f.GetType().Name);
    }
}
