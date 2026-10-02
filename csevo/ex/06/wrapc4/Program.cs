// 슬라이드 p6-v5-wrap-c4 — C# 5 의 세 가지 없이, C# 4.0
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

class App
{
    static void Log(string member, string msg)
    {
        Console.WriteLine(member + ": " + msg);
    }

    static Task<int> Fetch(string name)
    {
        return Task.Delay(10).ContinueWith(t => name.Length);
    }

    static Task<int> Total(string[] names)
    {
        List<Task<int>> tasks = new List<Task<int>>();
        foreach (string n in names) tasks.Add(Fetch(n));
        return Task.Factory.ContinueWhenAll(tasks.ToArray(), done =>
        {
            int[] sizes = done.Select(t => t.Result).ToArray();
            Log("Total", "sizes " + string.Join(",", sizes));
            List<Func<string>> later = new List<Func<string>>();
            foreach (string n in names)
            {
                string copy = n;        // the pre-C# 5 idiom
                later.Add(() => copy.ToUpper());
            }
            Log("Total", "names "
                + string.Join(",", later.Select(f => f())));
            return sizes.Sum();
        });
    }

    static void Main()
    {
        string[] names = { "ada", "grace", "alan" };
        Log("Main", "total " + Total(names).Result);
    }
}
