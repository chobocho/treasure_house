// 슬라이드 p6-v5-catchfinally — catch·finally 안의 await, C# 6.0
using System;
using System.Threading.Tasks;

class App
{
    static Task Log(string s)
    {
        Console.WriteLine("log: " + s);
        return Task.FromResult(0);
    }

    static async Task Work()
    {
        try { throw new InvalidOperationException("x"); }
        catch (InvalidOperationException) { await Log("catch"); }
        finally { await Log("finally"); }
    }

    static void Main()
    {
        Work().Wait();
    }
}
