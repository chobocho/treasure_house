// 슬라이드 p4-v3-ext-conv — 수신자에는 숫자 변환이 없다, C# 3.0
using System;

static class NumExt
{
    public static long Twice(this long x) { return x * 2; }
    public static string Kind(this object o)
    {
        return o.GetType().Name;
    }
}

class App
{
    static void Main()
    {
        int n = 5;
        Console.WriteLine(NumExt.Twice(n)); // static: int → long ok
        Console.WriteLine(n.Kind());        // receiver: boxing ok
        Console.WriteLine(n.Twice());       // receiver: int → long no
    }
}
