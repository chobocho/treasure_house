// 슬라이드 p6-v5-seqconc — 차례로 기다리기와 함께 기다리기, C# 5.0
using System;
using System.Threading;
using System.Threading.Tasks;

class App
{
    static int inFlight, peak;

    // Counts operations in flight; measures no time
    static async Task<int> Op(int x)
    {
        int now = Interlocked.Increment(ref inFlight);
        if (now > peak) peak = now;
        await Task.Delay(30);
        Interlocked.Decrement(ref inFlight);
        return x;
    }

    static async Task<int> OneByOne()
    {
        int a = await Op(1);            // next starts after this ends
        int b = await Op(2);
        return a + b;
    }

    static async Task<int> Together()
    {
        Task<int> ta = Op(1), tb = Op(2);   // start both first
        return await ta + await tb;
    }

    static void Main()
    {
        int r = OneByOne().Result;
        Console.WriteLine("one by one: " + r + ", peak " + peak);
        peak = 0;
        r = Together().Result;
        Console.WriteLine("together:   " + r + ", peak " + peak);
    }
}
