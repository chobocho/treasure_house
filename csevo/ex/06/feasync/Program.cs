// 슬라이드 p6-v5-fe-async — async 메서드 안의 foreach 포착, C# 5.0
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

class App
{
    // The loop body awaits; the lambdas still get one variable each.
    static async Task<List<Func<int>>> Collect(int[] items)
    {
        List<Func<int>> fs = new List<Func<int>>();
        foreach (int x in items)
        {
            await Task.Yield();
            fs.Add(() => x);
        }
        return fs;
    }

    static void Main()
    {
        List<Func<int>> fs = Collect(new[] { 1, 2, 3 }).Result;
        List<object> targets = new List<object>();
        foreach (Func<int> f in fs)
        {
            Console.Write(f() + " ");
            if (!targets.Contains(f.Target)) targets.Add(f.Target);
        }
        Console.WriteLine("| closure objects: " + targets.Count);
    }
}
