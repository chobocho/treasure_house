// 슬라이드 p8-v7-decon-ext — 확장 메서드 Deconstruct, C# 7.0
using System;
using System.Collections.Generic;

static class Ext
{
    // a type I don't own: DateTime
    public static void Deconstruct(this DateTime d,
        out int year, out int month, out int day)
    {
        year = d.Year; month = d.Month; day = d.Day;
    }
}

class App
{
    static void Main()
    {
        var (y, m, d) = new DateTime(2017, 3, 7);
        Console.WriteLine(y + "/" + m + "/" + d);

        var ages = new Dictionary<string, int> { ["Kim"] = 30 };
        foreach (var (name, age) in ages)       // KeyValuePair
            Console.WriteLine(name + " " + age);
        // .NET 10 declares it on the type itself
        var dm = typeof(KeyValuePair<string, int>)
            .GetMethod("Deconstruct");
        Console.WriteLine(dm.DeclaringType.Name + "." + dm.Name);
    }
}
