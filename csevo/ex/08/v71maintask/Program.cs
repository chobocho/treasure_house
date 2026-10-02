// 슬라이드 p8-v7_1-asyncmain-task — async 없는 Task<int> Main, C# 7.1
using System;
using System.Threading.Tasks;

class App
{
    static Task<int> Main()
    {
        Console.WriteLine("no async keyword");
        return Task.FromResult(3);
    }
}
