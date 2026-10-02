// 슬라이드 p10-sum-v9 — 같은 프로그램을 C# 9.0 으로, C# 9.0
using System;
using System.Collections.Generic;
using System.Linq;

List<Reading> list = new()
{
    new("Oslo", -3), new("Seoul", 12.5),
    new("Rome", 21), new("Cairo", 31),
};
Func<Reading, bool> warm = static r => r.Temp >= 15;
foreach (Reading r in list)
    Console.WriteLine($"{r.City,-6} {Label(r)}");
Console.WriteLine(list.Count(warm));
Reading rome = list[2] with { Temp = 22 };
Console.WriteLine(rome);
Console.WriteLine(rome.Equals(new Reading("Rome", 22)));
object o = list[0];
if (o is not null) Console.WriteLine("not null");

static string Label(Reading r) => r.Temp switch
{
    < 0 => "freezing",
    < 15 => "cool",
    < 25 => "mild",
    _ => "hot",
};

sealed record Reading(string City, double Temp);
