// 슬라이드 p6-v5-asyncstack — async 의 스택 트레이스, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static async Task<int> Inner()
    {
        await Task.Delay(1);
        throw new InvalidOperationException("deep failure");
    }

    static async Task<int> Outer()
    {
        int x = await Inner();
        return x + 1;
    }

    static void Main()
    {
        Outer().GetAwaiter().GetResult();   // unhandled: trace below
    }
}
