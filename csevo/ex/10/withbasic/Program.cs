// 슬라이드 p10-v9-with — with 식, C# 9.0
using System;

record Person(string FirstName, string LastName)
{
    public int Age { get; init; }
}
record Student(string FirstName, string LastName, int ID)
    : Person(FirstName, LastName);

class App
{
    static void Main()
    {
        var p = new Person("Mads", "Nielsen") { Age = 40 };
        var q = p with { LastName = "Torgersen", Age = 41 };
        Console.WriteLine(p);
        Console.WriteLine(q);
        var copy = p with { };               // plain copy
        Console.WriteLine(copy == p);
        Console.WriteLine(ReferenceEquals(copy, p));
        Person s = new Student("Ann", "Lee", 129);
        var s2 = s with { LastName = "Kim" };  // static type: Person
        Console.WriteLine(s2 is Student);
        Console.WriteLine(s2);
    }
}
