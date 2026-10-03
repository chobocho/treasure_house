// 슬라이드 p11-v10-asyncbuilder — 메서드·지역 함수·람다에 빌더, C# 10.0
using System;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

class App
{
    [AsyncMethodBuilder(typeof(LogBuilder<>))]
    static async Task<int> Twice(int x)
    {
        await Task.CompletedTask;            // completes synchronously
        return x * 2;
    }

    static async Task<int> Plain(int x) => await Task.FromResult(x);

    static void Main()
    {
        Console.WriteLine("method:");
        Console.WriteLine(Twice(21).Result);

        [AsyncMethodBuilder(typeof(LogBuilder<>))]
        async Task<string> Local() => await Task.FromResult("local");
        Console.WriteLine("local function:");
        Console.WriteLine(Local().Result);

        var lam = [AsyncMethodBuilder(typeof(LogBuilder<>))]
            async Task<int> () => 7;          // needs the return type
        Console.WriteLine("lambda:");
        Console.WriteLine(lam().Result);
        Console.WriteLine("plain: " + Plain(1).Result);
#if BAD
        Func<Task<int>> f = [AsyncMethodBuilder(typeof(LogBuilder<>))]
            async () => 8;
#endif
    }
}
