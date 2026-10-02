// 슬라이드 p10-v9-rec-nominal — 이름 있는 속성으로 쓰는 레코드, C# 9.0
using System;

public record Person
{
    public string FirstName { get; init; }
    public string LastName { get; init; }

    public string FullName => FirstName + " " + LastName;
    public Person Rename(string last) => this with { LastName = last };
}

class App
{
    static void Main()
    {
        var person = new Person
        {
            FirstName = "Mads", LastName = "Nielsen"
        };
        var other = person.Rename("Torgersen");
        Console.WriteLine(person);
        Console.WriteLine(other.FullName);
        Console.WriteLine(new Person());
    }
}
