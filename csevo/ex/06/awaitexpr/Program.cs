// 슬라이드 p6-v5-await-expr — await 는 식이다, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static Task<int> Get(string name, int value)
    {
        Console.WriteLine("  Get " + name);
        return Task.FromResult(value);
    }

    static int Add(int a, int b) { return a + b; }

    static async Task<string> Demo()
    {
        int s = Add(await Get("a", 1), await Get("b", 2));  // arguments
        if (await Get("c", 3) > s - 1)                    // condition
            s += 10;
        Task<Task<int>> nested = Task.FromResult(Get("d", 4));
        s += await await nested;                          // nested
        return "s = " + s;
    }

    static void Main()
    {
        Console.WriteLine(Demo().Result);
    }
}
