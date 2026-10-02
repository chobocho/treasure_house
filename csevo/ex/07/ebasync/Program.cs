// 슬라이드 p7-v6-eb-async — async 메서드도 =>, C# 6.0
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

class Program
{
    static async Task<int> TwiceAsync(int x)
        => await Task.FromResult(x) * 2;

    static Task<int> Twice(int x) => Task.FromResult(x * 2);

#if BAD
    static IEnumerable<int> One() => yield return 1;
#endif

    static void Main()
    {
        Console.WriteLine(TwiceAsync(20).Result + Twice(1).Result);
    }
}
