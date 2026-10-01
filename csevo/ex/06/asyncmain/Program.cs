// 슬라이드 p6-v5-asyncmain — 뒤 버전과의 맞물림: async Main, C# 7.1
using System;
using System.Threading.Tasks;

class App
{
    static async Task Main()
    {
        int x = await Task.FromResult(42);
        Console.WriteLine("async Main: " + x);
    }
}
