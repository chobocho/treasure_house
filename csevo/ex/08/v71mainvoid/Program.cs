// 슬라이드 p8-v7_1-asyncmain-void — async void Main, C# 7.1
using System;
using System.Threading.Tasks;

class App
{
    static async void Main()
    {
        await Task.Delay(1);
        Console.WriteLine("done");
    }
}
