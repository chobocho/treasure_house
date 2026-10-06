// 슬라이드 p14-v13-mg-cons — 제약을 못 맞추는 후보를 뺀다, C# 13
using System;

class C { }

static class E
{
    public static void M<T>(this C c, T x) where T : struct
        => Console.WriteLine("struct " + x);
    public static void M<T>(this C c, T x, int n) where T : class
        => Console.WriteLine("class " + x + n);
}

class Program
{
    static void Main()
    {
        var f = new C().M<string>;   // M<string>(T) breaks 'struct'
        f("s", 2);
        Console.WriteLine(f.GetType().Name);
    }
}
