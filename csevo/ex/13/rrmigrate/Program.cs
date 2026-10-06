// 슬라이드 p13-v12-rr-migrate — ref·in 을 ref readonly 로, C# 12.0
using System;

static class Lib            // version 1, or version 2 with -define:V2
{
#if V2
    public static int Peek(ref readonly int p) => p;   // was ref
    public static int Sum(ref readonly int p) => p + 1; // was in
#else
    public static int Peek(ref int p) => p;
    public static int Sum(in int p) => p + 1;
#endif
}

class App
{
    static void Main()
    {
        int x = 10;
        // callers written against version 1, never touched
        Console.WriteLine(Lib.Peek(ref x));
        Console.WriteLine(Lib.Sum(in x));
        Console.WriteLine(Lib.Sum(x));
    }
}
