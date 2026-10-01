// 슬라이드 p6-v5-lambda-nested — 안쪽 람다도 async 여야, C# 5.0
using System;
using System.Linq;
using System.Threading.Tasks;

class App
{
    static async Task<int> Sum(int[] xs)
    {
        Func<int, int> f = x => x + await Task.FromResult(1);
        Action g = async () => await Task.FromResult(2);  // fine
        g();
        return f(0) + xs.Sum();
    }

    static void Main() { }
}
