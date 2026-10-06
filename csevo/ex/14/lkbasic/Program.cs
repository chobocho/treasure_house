// 슬라이드 p14-v13-lock — Lock 객체, C# 13
using System;
using System.Threading;

class Program
{
    static readonly Lock gate = new Lock();
    static int count;

    static void Add()
    {
        lock (gate)
        {
            count++;
            Console.WriteLine("held: " + gate.IsHeldByCurrentThread);
        }
    }

    static void Main()
    {
        Add();
        Console.WriteLine("after: " + gate.IsHeldByCurrentThread);
        Console.WriteLine("count: " + count);
    }
}
