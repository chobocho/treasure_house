// 슬라이드 p6-v5-cs4014 — await 를 잊으면, C# 5.0
using System;
using System.IO;
using System.Threading.Tasks;

class App
{
    static async Task Save(string name)
    {
        await Task.FromResult(0);
        throw new IOException("disk full: " + name);
    }

    static async Task Run()
    {
        Save("a.txt");                  // forgot await
        Console.WriteLine("Run: saved?");
    }

    static void Main()
    {
        Run().Wait();                   // no exception
        Console.WriteLine("Main: done");
    }
}
