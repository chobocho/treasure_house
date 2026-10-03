// 슬라이드 p12-v11-required — required 멤버, C# 11
using System;

public class Person               // the blog's example
{
    public required string FirstName { get; init; }
    public string? MiddleName { get; init; }
    public required string LastName { get; init; }

    public override string ToString() =>
        FirstName + " " + (MiddleName ?? "-") + " " + LastName;
}

class Program
{
    static void Main()
    {
        var ada = new Person { FirstName = "Ada", LastName = "L." };
        Console.WriteLine(ada);
#if BAD
        var person = new Person { FirstName = "Ada" };  // no LastName
#endif
    }
}
