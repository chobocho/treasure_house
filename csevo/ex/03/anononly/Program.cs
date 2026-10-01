// 슬라이드 p3-v2-anon-only — 람다에 없는 한 가지, C# 14
using System;

delegate void Three(int a, string b, double c);

class App
{
    static void Main()
    {
        Three t1 = delegate { Console.WriteLine("anon"); };
        Three t2 = (_, _, _) => Console.WriteLine("lambda");
        EventHandler h1 = delegate { Console.WriteLine("anon"); };
        EventHandler h2 = (s, e) => Console.WriteLine("lambda");
        t1(1, "x", 2.0);
        t2(1, "x", 2.0);
        h1(null, EventArgs.Empty);
        h2(null, EventArgs.Empty);
    }
}
