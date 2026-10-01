// 슬라이드 p6-v5-gate — async 메서드, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static async Task<int> AddLater(int a, int b)
    {
        await Task.Delay(10);
        return a + b;
    }

    static void Main()
    {
        Task<int> t = AddLater(2, 3);
        Console.WriteLine("sum = " + t.GetAwaiter().GetResult());
    }
}
