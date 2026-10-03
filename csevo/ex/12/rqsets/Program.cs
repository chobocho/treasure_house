// 슬라이드 p12-v11-rq-sets — [SetsRequiredMembers], C# 11
using System;
using System.Diagnostics.CodeAnalysis;

class Person
{
    public required string First { get; init; }
    public required string Last { get; init; }

    public Person() { }

    [SetsRequiredMembers]
    public Person(string first, string last)
    { First = first; Last = last; }

    [SetsRequiredMembers]            // not checked: sets nothing
    public Person(int id) { }
#if BAD
    public Person(string full) : this(full, full) { }
#endif
}

class Program
{
    static void Main()
    {
        Console.WriteLine(new Person("Ada", "Lovelace").Last);
        Console.WriteLine(new Person { First = "A", Last = "T." }.Last);
        var ghost = new Person(7);
        Console.WriteLine(ghost.Last ?? "(Last is null)");
#if BAD2
        var p = new Person();
#endif
    }
}
