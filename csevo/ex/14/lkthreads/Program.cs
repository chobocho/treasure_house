// 슬라이드 p14-v13-lk-threads — 네 스레드가 같은 Lock 을 쓴다, C# 13
using System;
using System.Threading;

class Program
{
    static readonly Lock gate = new();
    static long total;

    static void Work()
    {
        for (int i = 0; i < 100_000; i++)
        {
            lock (gate) { total++; }
        }
    }

    static void Main()
    {
        var threads = new Thread[4];
        for (int i = 0; i < threads.Length; i++)
        {
            threads[i] = new Thread(Work);
            threads[i].Start();
        }
        foreach (Thread t in threads) t.Join();
        Console.WriteLine("total " + total);   // always 400000
        Console.WriteLine("held after join: "
            + gate.IsHeldByCurrentThread);
    }
}
