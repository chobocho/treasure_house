// 슬라이드 p3-v2-closure — 잡힌 바깥 변수, C# 2.0
using System;

delegate int Counter();

class App
{
    static Counter Make()
    {
        int x = 0;                       // a local of Make
        return delegate { return ++x; };
    }

    static void Main()
    {
        Counter a = Make();
        Console.WriteLine(a());
        Console.WriteLine(a());
        Console.WriteLine(a());          // Make returned long ago
        Counter b = Make();
        Console.WriteLine(b());          // a new x
    }
}
