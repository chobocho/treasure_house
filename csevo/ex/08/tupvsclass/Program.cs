// 슬라이드 p8-v7-tuple-vs — System.Tuple 과 System.ValueTuple, C# 7.0
using System;
using System.Linq;

class App
{
    static void Show(Type t)
    {
        string kind = t.IsValueType ? "struct" : "class";
        string fields = string.Join(",", t.GetFields()
            .Select(f => f.Name + (f.IsInitOnly ? "(ro)" : "")));
        string props = string.Join(",", t.GetProperties()
            .Where(p => p.DeclaringType == t).Select(p => p.Name));
        Console.WriteLine("{0,-12} {1,-6} fields[{2}] props[{3}]",
            t.Name, kind, fields, props);
    }

    static void Main()
    {
        Show(typeof(Tuple<int, string>));     // C# 4 era library type
        Show(typeof((int, string)));          // C# 7.0 tuple syntax
        var old = Tuple.Create(1, "a");
        var now = (1, "a");
        now.Item1 = 2;                        // a public field
        Console.WriteLine(old + " " + now);
#if BAD
        old.Item1 = 2;                        // a get-only property
#endif
    }
}
