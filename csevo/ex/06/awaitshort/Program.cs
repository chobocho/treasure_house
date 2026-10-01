// 슬라이드 p6-v5-awaitshort — && 의 오른쪽 await, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static Task<bool> Check(string name, bool value)
    {
        Console.WriteLine("  Check " + name);
        return Task.FromResult(value);
    }

    static async Task<string> Demo(bool first)
    {
        bool ok = await Check("a", first) && await Check("b", true);
        string s = first ? await Check("c", true) + "" : "skipped";
        return ok + " " + s;
    }

    static void Main()
    {
        Console.WriteLine("first = true:");
        Console.WriteLine(Demo(true).Result);
        Console.WriteLine("first = false:");
        Console.WriteLine(Demo(false).Result);
    }
}
