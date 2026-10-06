// 슬라이드 p14-v13-ru-lower — 상태 기계에 안 오르는 지역, C# 13.0
using System;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;

class App
{
    static async Task<int> Work(string text)
    {
        int keep = text.Length;               // used after await
        ReadOnlySpan<char> s = text.AsSpan(); // never crosses await
        int first = s[0];
        await Task.Yield();
        return keep + first;
    }

    static void Main()
    {
        Console.WriteLine(Work("A!").Result);
        var sm = typeof(App).GetNestedTypes(BindingFlags.NonPublic)
            .Single(t => t.Name.Contains("Work"));
        Console.WriteLine(sm.Name
            + (sm.IsValueType ? " struct" : " class"));
        var all = BindingFlags.Instance | BindingFlags.Public
            | BindingFlags.NonPublic;
        foreach (var f in sm.GetFields(all).OrderBy(f => f.Name,
                     StringComparer.Ordinal))
            Console.WriteLine($"  {f.FieldType.Name,-24} {f.Name}");
    }
}
