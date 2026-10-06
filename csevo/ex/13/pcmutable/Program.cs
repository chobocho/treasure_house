// 슬라이드 p13-v12-pc-mutable — 매개변수는 바꿀 수 있는 변수다, C# 12.0
using System;

class Ticket(int next)
{
    public int Take() => next++;          // the captured variable
    public void Reset() => next = 0;      // assignable, too
}

class App
{
    static void Main()
    {
        var t = new Ticket(100);
        Console.WriteLine($"{t.Take()} {t.Take()} {t.Take()}");
        t.Reset();
        Console.WriteLine(t.Take());
    }
}
