// 슬라이드 p9-v8-asyncusing — await using 과 닫는 차례, C# 8.0
using System;
using System.Threading.Tasks;

class Res : IAsyncDisposable
{
    string name;
    public Res(string name)
    {
        this.name = name;
        Console.WriteLine("open " + name);
    }
    public async ValueTask DisposeAsync()
    {
        await Task.Yield();
        Console.WriteLine("close " + name);
    }
}

class App
{
    static async Task Main()
    {
        await using (Res a = new Res("a"), b = new Res("b"))
        {
            Console.WriteLine("  body 1");
        }
        await using var c = new Res("c");
        await using var d = new Res("d");
        Console.WriteLine("  body 2");
    }
}
