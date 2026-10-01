// 슬라이드 p3-v2-reentry — 처리기 안에서 구독을 끊으면, C# 2.0
using System;

class Bus
{
    public event EventHandler Fired;
    public void Fire(string round)
    {
        Console.WriteLine(round);
        if (Fired != null) Fired(this, EventArgs.Empty);
    }
}

class App
{
    static void Main()
    {
        Bus bus = new Bus();
        EventHandler once = null;
        once = delegate
        {
            Console.WriteLine("  once (unsubscribes)");
            bus.Fired -= once;
        };
        bus.Fired += once;
        bus.Fired += delegate { Console.WriteLine("  always"); };

        bus.Fire("round 1");     // runs the list read before -=
        bus.Fire("round 2");
    }
}
