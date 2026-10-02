// 슬라이드 p10-sum-v8 — 같은 프로그램을 C# 8.0 으로, C# 8.0
using System;
using System.Collections.Generic;
using System.Linq;

sealed class Reading : IEquatable<Reading>
{
    public string City { get; }
    public double Temp { get; }
    public Reading(string c, double t) { City = c; Temp = t; }
    public Reading WithTemp(double t) => new Reading(City, t);
    public bool Equals(Reading other) =>
        other != null && City == other.City && Temp == other.Temp;
    public override bool Equals(object obj) => Equals(obj as Reading);
    public override int GetHashCode() => HashCode.Combine(City, Temp);
    public override string ToString() =>
        $"Reading {{ City = {City}, Temp = {Temp} }}";
}

class Program
{
    static string Label(Reading r) => r.Temp switch
    {
        double t when t < 0 => "freezing",
        double t when t >= 0 && t < 15 => "cool",
        double t when t >= 15 && t < 25 => "mild",
        _ => "hot",
    };

    static void Main()
    {
        var list = new List<Reading>
        {
            new Reading("Oslo", -3), new Reading("Seoul", 12.5),
            new Reading("Rome", 21), new Reading("Cairo", 31),
        };
        Func<Reading, bool> warm = r => r.Temp >= 15;
        foreach (Reading r in list)
            Console.WriteLine($"{r.City,-6} {Label(r)}");
        Console.WriteLine(list.Count(warm));
        Reading rome = list[2].WithTemp(22);
        Console.WriteLine(rome);
        Console.WriteLine(rome.Equals(new Reading("Rome", 22)));
        object o = list[0];
        if (!(o is null)) Console.WriteLine("not null");
    }
}
