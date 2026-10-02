// 슬라이드 p9-v8-as-sm — 비동기 반복기의 필드(구현 세부), C# 8.0
using System;
using System.Collections.Generic;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;

class App
{
    static async IAsyncEnumerable<int> Gen(int n,
        [EnumeratorCancellation] CancellationToken ct)
    {
        for (int i = 0; i < n; i++)
        {
            await Task.Yield();
            yield return i;
        }
    }

    static void Main()
    {
        Type t = Gen(1, default).GetType();
        Console.WriteLine(t.Name);
        var lines = new List<string>();
        foreach (FieldInfo f in t.GetFields(BindingFlags.Instance |
                 BindingFlags.Public | BindingFlags.NonPublic))
            lines.Add(string.Format("  {0,-34} {1}", f.Name,
                f.FieldType.Name));
        lines.Sort(string.CompareOrdinal);
        foreach (string s in lines)
            Console.WriteLine(s);
    }
}
