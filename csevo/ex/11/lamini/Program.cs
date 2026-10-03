// 슬라이드 p11-v10-la-mini — Delegate 를 받는 작은 라우터, C# 10.0
using System;
using System.Collections.Generic;
using System.Reflection;

class GetAttribute : Attribute
{
    public string Path;
    public GetAttribute(string path) { Path = path; }
}

class App
{
    static readonly Dictionary<string, Delegate> routes = new();

    // like ASP.NET Core's MapGet(string, Delegate): no Func<...> cast
    static void Map(Delegate handler)
    {
        var get = handler.Method.GetCustomAttribute<GetAttribute>();
        routes[get.Path] = handler;
    }

    static void Call(string path, params string[] query)
    {
        Delegate h = routes[path];
        ParameterInfo[] ps = h.Method.GetParameters();
        var args = new object[ps.Length];
        for (int i = 0; i < ps.Length; i++)          // bind by position
            args[i] = Convert.ChangeType(query[i], ps[i].ParameterType);
        Console.WriteLine($"{path,-7}{string.Join(",", query),-6}" +
                          $"-> {h.DynamicInvoke(args)}");
    }

    static void Main()
    {
        Map([Get("/hello")] (string name) => $"hello {name}");
        Map([Get("/add")] (int a, int b) => a + b);
        Call("/hello", "fold");
        Call("/add", "2", "40");
    }
}
