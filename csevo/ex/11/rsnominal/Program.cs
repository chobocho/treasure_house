// 슬라이드 p11-v10-rs-nominal — 목록 없는 record struct, C# 10.0
using System;

public readonly record struct Person
{
    public string FirstName { get; init; }
    public string LastName { get; init; }
}

class App
{
    static void Main()
    {
        var p = new Person
            { FirstName = "Mads", LastName = "Torgersen" };
        var q = p with { LastName = "Kristensen" };
        Console.WriteLine(p);
        Console.WriteLine(q);
        Console.WriteLine(new Person());
        Console.WriteLine(
            typeof(Person).GetMethod("Deconstruct") == null);
    }
}
