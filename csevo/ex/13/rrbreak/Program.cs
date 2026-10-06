// 슬라이드 p13-v12-rr-break — ref 인수가 in 매개변수에 맞는다, C# 12.0
using System;

class C
{
    public string M(in int i) => "C";
}

static class E
{
    public static string M(this C c, ref int i) => "E";
}

interface I1 { }
interface I2 { }

static class K
{
    public static string M(I1 o, ref int x) => "1";
    public static string M(I2 o, in int x) => "2";
}

class App
{
    static void Main()
    {
        var i = 5;
#pragma warning disable CS9191   // 'ref' for an 'in' parameter
        Console.WriteLine(new C().M(ref i));
#pragma warning restore CS9191
        Console.WriteLine(E.M(new C(), ref i));     // workaround
#if BAD
        Console.WriteLine(K.M(null, ref i));
#endif
        Console.WriteLine(K.M((I1)null, ref i));    // workaround
    }
}
