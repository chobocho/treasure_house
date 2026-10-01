// 슬라이드 p2-v1-eventimmut — 대리자는 바뀌지 않는 객체, C# 1.0
using System;

delegate void Tick();

class Clock
{
    public event Tick Ticked;
    public void Fire()
    {
        Tick h = Ticked;                 // this list is fixed now
        if (h != null) h();
    }
}

class App
{
    static Clock clock = new Clock();
    static int n;

    static void Once()
    {
        Console.WriteLine("  Once runs, unsubscribes itself and Late");
        clock.Ticked -= new Tick(Once);
        clock.Ticked -= new Tick(Late);
    }
    static void Late() { Console.WriteLine("  Late runs anyway"); }

    static void Main()
    {
        clock.Ticked += new Tick(Once);
        clock.Ticked += new Tick(Late);
        for (n = 1; n <= 2; n++)
        {
            Console.WriteLine("fire " + n + ":");
            clock.Fire();
        }
    }
}
