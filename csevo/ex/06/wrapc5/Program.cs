// 슬라이드 p6-v5-wrap-c5 — 같은 프로그램을 C# 5 로, C# 5.0
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

class App
{
    static void Log(string msg, [CallerMemberName] string member = "")
    {
        Console.WriteLine(member + ": " + msg);
    }

    static async Task<int> Fetch(string name)
    {
        await Task.Delay(10);
        return name.Length;
    }

    static async Task<int> Total(string[] names)
    {
        List<Task<int>> tasks = new List<Task<int>>();
        foreach (string n in names) tasks.Add(Fetch(n));
        int[] sizes = await Task.WhenAll(tasks);
        Log("sizes " + string.Join(",", sizes));
        List<Func<string>> later = new List<Func<string>>();
        foreach (string n in names) later.Add(() => n.ToUpper());
        Log("names " + string.Join(",", later.Select(f => f())));
        return sizes.Sum();
    }

    static void Main()
    {
        string[] names = { "ada", "grace", "alan" };
        Log("total " + Total(names).Result);
    }
}
