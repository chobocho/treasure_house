// 슬라이드 p9-v8-as-pattern — 인터페이스 없이 await foreach, C# 8.0
using System;
using System.Threading.Tasks;

class Countdown                     // implements no interface
{
    int from;
    public Countdown(int from) { this.from = from; }
    public Enumerator GetAsyncEnumerator() => new Enumerator(from);

    public struct Enumerator        // a struct: no allocation
    {
        int n;
        public Enumerator(int n) { this.n = n + 1; }
        public int Current => n;
        public ValueTask<bool> MoveNextAsync() =>
            new ValueTask<bool>(--n > 0);
        public ValueTask DisposeAsync()
        {
            Console.WriteLine("DisposeAsync (found by name)");
            return default;
        }
    }
}

class App
{
    static async Task Main()
    {
        await foreach (int i in new Countdown(3))
            Console.WriteLine(i);
    }
}
