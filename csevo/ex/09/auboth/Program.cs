// 슬라이드 p9-v8-au-both — Dispose 와 DisposeAsync 를 다 가지면, C# 8.0
using System;
using System.Threading.Tasks;

class File2 : IDisposable, IAsyncDisposable
{
    public void Dispose() => Console.WriteLine("  Dispose");
    ValueTask IAsyncDisposable.DisposeAsync()
    {
        Console.WriteLine("  IAsyncDisposable.DisposeAsync");
        return default;
    }
    public ValueTask DisposeAsync()          // public, found by name
    {
        Console.WriteLine("  public DisposeAsync");
        return default;
    }
}

class App
{
    static async Task Main()
    {
        Console.WriteLine("using:");
        using (new File2()) { }
        Console.WriteLine("await using:");
        await using (new File2()) { }
        Console.WriteLine("await using via the interface:");
        await using (IAsyncDisposable f = new File2()) { }
    }
}
