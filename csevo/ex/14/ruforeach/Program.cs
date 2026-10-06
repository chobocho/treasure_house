// 슬라이드 p14-v13-ru-foreach — await 사이의 foreach 등, C# 13.0
using System;
using System.Threading;
using System.Threading.Tasks;

ref struct Scope
{
    public void Dispose() => Console.WriteLine("scope closed");
}

class App
{
    static readonly Lock gate = new Lock();
    static int[] data = { 1, 2, 3 };

    static async Task<int> Step()
    {
        await Task.Yield();
        Span<int> span = data;
        foreach (ref int x in span) x *= 10;    // ref variable
        using (new Scope()) { }                 // ref struct resource
        lock (gate) { data[0]++; }              // ref struct Scope
        await Task.Yield();
        return data[0] + data[1] + data[2];
    }

    static void Main() => Console.WriteLine(Step().Result);
}
