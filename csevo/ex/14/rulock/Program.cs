// 슬라이드 p14-v13-ru-lock — 반복기의 lock 안에서 yield, C# 13.0
using System;
using System.Collections.Generic;
using System.Threading;

class App
{
#if LOCK
    static readonly Lock gate = new Lock();     // C# 13 Lock object
    static bool Held() => gate.IsHeldByCurrentThread;
#else
    static readonly object gate = new object();
    static bool Held() => Monitor.IsEntered(gate);
#endif

    static IEnumerable<int> Locked()
    {
        lock (gate)
        {
            yield return 1;       // the lock stays held while suspended
        }
    }

    static void Main()
    {
        foreach (int x in Locked())
            Console.WriteLine(x + " held: " + Held());
        Console.WriteLine("after: " + Held());
    }
}
