// 슬라이드 p13-v12-brk-asyncusing — await using 의 선택, C# 12.0
using System;
using System.Threading.Tasks;

class C : IAsyncDisposable
{
    ValueTask IAsyncDisposable.DisposeAsync()
    {
        Console.WriteLine("interface DisposeAsync");
        return default;
    }

    public ValueTask DisposeAsync()
    {
        Console.WriteLine("public DisposeAsync");
        return default;
    }
}

class App
{
    static async Task Main()
    {
        await using (var x = new C()) { }
        await using (IAsyncDisposable y = new C()) { }
    }
}
