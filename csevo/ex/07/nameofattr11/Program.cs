// 슬라이드 p7-v6-nameof-attr11 — 특성 안의 매개변수 이름, C# 11.0
using System;
using System.Diagnostics.CodeAnalysis;
using System.Reflection;

class Cache
{
    string value = "cached";

    [return: NotNullIfNotNull(nameof(fallback))]
    public string Get(string fallback) => value ?? fallback;

    public bool TryGet([NotNullWhen(true)] out string result)
    {
        result = value;
        return true;
    }
}

class App
{
    static void Main()
    {
        MethodInfo m = typeof(Cache).GetMethod("Get");
        var a = m.ReturnParameter
            .GetCustomAttribute<NotNullIfNotNullAttribute>();
        Console.WriteLine("ParameterName = " + a.ParameterName);
        Console.WriteLine(new Cache().Get(null));
    }
}
