// 슬라이드 p9-v8-nrt-embed — NullableAttribute 는 어디서 오나, C# 8.0
#nullable enable
using System;
using System.Linq;

public class C
{
    public string? Name;
}

class App
{
    static void Main()
    {
        Type na = typeof(C).GetField("Name")!.CustomAttributes
            .First().AttributeType;
        Console.WriteLine(na.FullName);
        Console.WriteLine("assembly : " + na.Assembly.GetName().Name);
        Console.WriteLine("public   : " + na.IsPublic);
        foreach (var a in na.CustomAttributes)
            Console.WriteLine("marked   : " + a.AttributeType.Name);
        Console.WriteLine("types in this assembly:");
        foreach (Type t in typeof(App).Assembly.GetTypes())
            Console.WriteLine("  " + t.FullName);
    }
}
