// 슬라이드 p6-v5-valuetask — 뒤 버전과의 맞물림: ValueTask 반환, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    // task-like return types are listed as a C# 7 feature
    static async ValueTask<int> Twice(int x)
    {
        await Task.FromResult(0);
        return x * 2;
    }

    static void Main()
    {
        ValueTask<int> v = Twice(21);
        Console.WriteLine(v.IsCompleted + " " + v.Result);
    }
}
