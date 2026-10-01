// 슬라이드 p6-v5-awaitplaces — await 가 못 가는 자리, C# 5.0
using System;
using System.Linq.Expressions;
using System.Threading.Tasks;

class App
{
    static async Task InUnsafe()
    {
        unsafe { int x = await Task.FromResult(1); }
    }

    static void InTree()
    {
        Expression<Func<Task<int>>> e =
            async () => await Task.FromResult(1);
    }

    static void Main() { }
}
