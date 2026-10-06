// 슬라이드 p14-v13-lk-object — Lock 을 object 로 바꾸면, C# 13
using System;
using System.Threading;

class Program
{
    static readonly Lock gate = new();

    static void Main()
    {
        object o = gate;                    // warning here
        lock (o)                            // Monitor-based lock
        {
            Console.WriteLine("lock (o):    Lock held "
                + gate.IsHeldByCurrentThread
                + ", Monitor held " + Monitor.IsEntered(o));
        }
        lock (gate)                         // Lock.EnterScope
        {
            Console.WriteLine("lock (gate): Lock held "
                + gate.IsHeldByCurrentThread
                + ", Monitor held " + Monitor.IsEntered(gate));
        }
        if (gate != null)                   // no warning
            Console.WriteLine("gate != null");
    }
}
