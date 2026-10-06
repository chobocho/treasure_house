// 슬라이드 p14-v13-lk-scope — lock 없이 Lock 쓰기, C# 13
using System;
using System.Threading;

class Program
{
    static readonly Lock gate = new();

    static void Main()
    {
        using (gate.EnterScope())       // what lock (gate) becomes
        {
            Console.WriteLine("scope: " + gate.IsHeldByCurrentThread);
        }
        gate.Enter();                   // Enter/Exit by hand
        gate.Enter();                   // re-entrant on one thread
        Console.WriteLine("twice: " + gate.IsHeldByCurrentThread);
        gate.Exit();
        Console.WriteLine("once:  " + gate.IsHeldByCurrentThread);
        gate.Exit();
        Console.WriteLine("none:  " + gate.IsHeldByCurrentThread);
        if (gate.TryEnter())
        {
            Console.WriteLine("TryEnter: true");
            gate.Exit();
        }
        try { gate.Exit(); }            // not held
        catch (Exception e) { Console.WriteLine(e.GetType().Name); }
    }
}
