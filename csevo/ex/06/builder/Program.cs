// 슬라이드 p6-v5-builder — 표준의 빌더 패턴과 .NET 10 의 빌더, C# 5.0
using System;
using System.Collections.Generic;
using System.Reflection;
using System.Runtime.CompilerServices;

class App
{
    static void Main()
    {
        // the members the standard's task-builder pattern requires
        string[] pattern = { "Create", "Start", "SetStateMachine",
            "SetException", "SetResult", "AwaitOnCompleted",
            "AwaitUnsafeOnCompleted", "get_Task" };
        Type b = typeof(AsyncTaskMethodBuilder<int>);
        List<string> have = new List<string>();
        foreach (MethodInfo m in b.GetMethods(BindingFlags.Public
            | BindingFlags.Instance | BindingFlags.Static
            | BindingFlags.DeclaredOnly))
        {
            if (!have.Contains(m.Name)) have.Add(m.Name);
        }
        foreach (string p in pattern)
            Console.WriteLine("{0,-24} {1}", p, have.Contains(p));
        have.RemoveAll(n => Array.IndexOf(pattern, n) >= 0);
        have.Sort(StringComparer.Ordinal);
        Console.WriteLine("others: "
            + (have.Count == 0 ? "(none)" : string.Join(", ", have)));
        Console.WriteLine("value type? " + b.IsValueType);
    }
}
