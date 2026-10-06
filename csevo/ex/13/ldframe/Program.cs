// 슬라이드 p13-v12-ld-frame — 프레임워크가 기본값을 읽는 법, C# 12
using System;
using System.Collections.Generic;
using System.Reflection;

class Program
{
    // a tiny "MapGet": fill parameters from a query, else defaults
    static object Call(Delegate handler, Dictionary<string, string> q)
    {
        ParameterInfo[] ps = handler.Method.GetParameters();
        var args = new object[ps.Length];
        for (int i = 0; i < ps.Length; i++)
            args[i] = q.TryGetValue(ps[i].Name, out string v)
                ? Convert.ChangeType(v, ps[i].ParameterType)
                : ps[i].HasDefaultValue ? ps[i].DefaultValue
                : throw new ArgumentException("missing " + ps[i].Name);
        return handler.DynamicInvoke(args);
    }

    static void Main()
    {
        var todo = (int id, string task = "foo") => id + ":" + task;
        Console.WriteLine(Call(todo, new() { ["id"] = "7" }));
        Console.WriteLine(Call(todo,
            new() { ["id"] = "8", ["task"] = "bar" }));
        try { Call(todo, new()); }
        catch (ArgumentException e) { Console.WriteLine(e.Message); }
    }
}
