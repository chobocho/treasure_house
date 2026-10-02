// 슬라이드 p9-v8-nrt-async — Task<string?> 과 await, C# 8.0
#nullable enable
using System;
using System.Threading.Tasks;

class App
{
    static Task<string?> FindAsync(int id) =>
        Task.FromResult(id == 1 ? "Ada" : (string?)null);

    static async Task<string> NameAsync(int id)
    {
        string? n = await FindAsync(id);
        return n ?? "unknown";
    }

    static async Task Main()
    {
        string s = await FindAsync(2);      // CS8600
        Task<string> t = FindAsync(1);      // CS8619
        Console.WriteLine((s ?? "null") + " " + await t);
        Console.WriteLine(await NameAsync(2));
    }
}
