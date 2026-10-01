// 슬라이드 p6-v5-awaitnull — null Task 를 await 하면, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    // not async: nothing stops it from returning null
    static Task<int> Lookup(string key)
    {
        if (key == "missing") return null;
        return Task.FromResult(key.Length);
    }

    static async Task<string> Demo(string key)
    {
        try { return key + " -> " + await Lookup(key); }
        catch (NullReferenceException)
        {
            return key + " -> NullReferenceException";
        }
    }

    static void Main()
    {
        Console.WriteLine(Demo("abc").Result);
        Console.WriteLine(Demo("missing").Result);
    }
}
