// 슬라이드 p6-v5-after-streamsm — 비동기 반복기가 만드는 클래스, C# 8.0
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

class App
{
    static async IAsyncEnumerable<int> One()
    {
        await Task.Yield();
        yield return 1;
    }

    static void Main()
    {
        IAsyncEnumerable<int> s = One();
        Type t = s.GetType();
        Console.WriteLine("class: " + t.Name);
        List<string> names = new List<string>();
        foreach (Type i in t.GetInterfaces()) names.Add(i.Name);
        names.Sort(string.CompareOrdinal);
        foreach (string n in names) Console.WriteLine("  " + n);
        Console.WriteLine("same object as enumerator: "
            + ReferenceEquals(s, s.GetAsyncEnumerator()));
    }
}
