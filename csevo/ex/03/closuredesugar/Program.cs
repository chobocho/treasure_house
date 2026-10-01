// 슬라이드 p3-v2-closure-desugar — 클래스로 풀어 쓰기, C# 2.0
using System;

delegate int Counter();

class Locals1                    // the standard's "__Locals1"
{
    public int x;
    public int Method1() { return ++x; }
}

class App
{
    static Counter MakeAnon()
    {
        int x = 0;
        return delegate { return ++x; };
    }

    static Counter MakeByHand()
    {
        Locals1 locals1 = new Locals1();   // the local moves here
        locals1.x = 0;
        return new Counter(locals1.Method1);
    }

    static void Main()
    {
        Counter a = MakeAnon();
        Counter b = MakeByHand();
        for (int i = 0; i < 3; i++)
            Console.WriteLine(a() + " " + b());
    }
}
