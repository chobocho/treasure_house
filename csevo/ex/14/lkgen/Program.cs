// 슬라이드 p14-v13-lk-generic — 형식 매개변수로 넘긴 Lock, C# 13
using System;
using System.Collections.Generic;
using System.Threading;

class Program
{
    static void Guard<T>(T x, Lock probe) where T : class
    {
        lock (x)                            // always Monitor
        {
            Console.WriteLine("Lock held " + probe.IsHeldByCurrentThread
                + ", Monitor held " + Monitor.IsEntered(x));
        }
    }

    static void Main()
    {
        var gate = new Lock();
        Guard(gate, gate);                  // no warning
        var list = new List<Lock> { gate }; // no warning either
        Console.WriteLine(list.Count);
    }
}
