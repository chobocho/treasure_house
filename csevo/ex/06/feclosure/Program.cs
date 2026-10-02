// 슬라이드 p6-v5-fe-closure — 반복마다 새 클로저 객체, C# 5.0
using System;
using System.Collections.Generic;

class App
{
    // How many distinct closure objects do the delegates point to?
    static void Count(string tag, List<Func<int>> fs)
    {
        List<object> seen = new List<object>();
        foreach (Func<int> f in fs)
            if (!seen.Contains(f.Target)) seen.Add(f.Target);
        Console.WriteLine(tag + fs.Count + " delegates, "
            + seen.Count + " closure object(s) of "
            + seen[0].GetType().Name);
    }

    static void Main()
    {
        int[] items = { 1, 2, 3 };
        List<Func<int>> a = new List<Func<int>>();
        foreach (int x in items) a.Add(() => x);
        Count("foreach: ", a);

        List<Func<int>> b = new List<Func<int>>();
        for (int i = 0; i < 3; i++) b.Add(() => i);
        Count("for:     ", b);
    }
}
