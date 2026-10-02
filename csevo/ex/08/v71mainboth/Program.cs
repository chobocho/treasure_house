// 슬라이드 p8-v7_1-asyncmain-both — 옛 Main 이 있으면, C# 7.1
using System;
using System.Threading.Tasks;

class App
{
    static void Main()
    {
        Console.WriteLine("void Main");
    }

    static async Task Main(string[] args)
    {
        await Task.Yield();
        Console.WriteLine("async Task Main");
    }
}
