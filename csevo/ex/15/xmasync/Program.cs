// 슬라이드 p15-v14-xm-async — 확장 블록 안의 async 와 반복기, C# 14
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;

static class AsyncExt
{
    extension(IAsyncEnumerable<int> values)
    {
        public async Task<int> SumAsync()
        {
            int sum = 0;
            await foreach (int v in values) sum += v;
            return sum;
        }
    }

    extension(int n)
    {
        public async IAsyncEnumerable<int> Upto()
        {
            for (int i = 1; i <= n; i++)
            {
                await Task.Yield();
                yield return i;
            }
        }
    }
}

class Program
{
    static async Task Main()
    {
        Console.WriteLine(await 4.Upto().SumAsync());
        foreach (Type t in typeof(AsyncExt).GetNestedTypes(
                     BindingFlags.NonPublic).OrderBy(t => t.Name))
            Console.WriteLine(t.Name);
    }
}
