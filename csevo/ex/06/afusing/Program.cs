// 슬라이드 p6-v5-after-using — await using 과 IAsyncDisposable, C# 8.0
using System;
using System.Threading.Tasks;

class Conn : IAsyncDisposable
{
    readonly string name;
    public Conn(string name) { this.name = name; Say("open"); }
    void Say(string s) { Console.WriteLine(name + ": " + s); }

    public async ValueTask DisposeAsync()
    {
        await Task.Yield();             // e.g. flush over the network
        Say("closed (awaited)");
    }
}

class App
{
    static async Task Main()
    {
        await using (Conn a = new Conn("a"))
        {
            Console.WriteLine("work with a");
        }

        await using Conn b = new Conn("b");    // a using declaration
        Console.WriteLine("work with b");
        Console.WriteLine("end of Main");
    }
}
