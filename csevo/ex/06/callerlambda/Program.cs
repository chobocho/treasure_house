// 슬라이드 p6-v5-caller-lambda — 람다·반복기·async 안에서, C# 5.0
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using System.Runtime.CompilerServices;

class App
{
    static string N([CallerMemberName] string m = "?") { return m; }

    static IEnumerable<string> Items()
    {
        yield return "iterator   -> " + N();
    }

    static async Task<string> LoadAsync()
    {
        await Task.Yield();
        return "async      -> " + N();
    }

    static void Main()
    {
        Func<string> f = () => "lambda     -> " + N();
        Func<string> g = delegate { return "anonymous  -> " + N(); };
        Console.WriteLine(f());
        Console.WriteLine(g());
        foreach (string s in Items()) Console.WriteLine(s);
        Console.WriteLine(LoadAsync().Result);
        Console.WriteLine("generated  -> " + f.Method.Name);
    }
}
