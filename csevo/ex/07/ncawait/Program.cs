// 슬라이드 p7-v6-nullcond-await — await 와 ?. 의 함정, C# 6.0
using System;
using System.Threading.Tasks;

class Client
{
    public Task<int> FetchAsync() { return Task.FromResult(42); }
}

class App
{
    static async Task<string> Run(Client c)
    {
        try
        {
            int? n = await c?.FetchAsync();     // await null
            return "got " + n;
        }
        catch (NullReferenceException)
        {
            return "NullReferenceException";
        }
    }

    static async Task<string> Safe(Client c)
    {
        Task<int> t = c?.FetchAsync();
        return t == null ? "no client" : "got " + await t;
    }

    static void Main()
    {
        Console.WriteLine(Run(new Client()).Result);
        Console.WriteLine(Run(null).Result);
        Console.WriteLine(Safe(null).Result);
    }
}
