// 슬라이드 p7-v6-boiler6 — 같은 클래스를 C# 6 으로, C# 6.0
using System;

class Address { public string City; }

class Person
{
    public string First, Last;
    public Address Home;

    public Person(string first, string last)
    {
        if (first == null)
            throw new ArgumentNullException(nameof(first));
        First = first;
        Last = last;
    }

    public string Describe()
    {
        return $"{First} {Last} ({Home?.City ?? "no address"})";
    }
}

class App
{
    static void Main()
    {
        Person a = new Person("Ada", "Lovelace");
        a.Home = new Address { City = "London" };
        Console.WriteLine(a.Describe());
        Console.WriteLine(new Person("Alan", "Turing").Describe());
        try { new Person(null, "X"); }
        catch (ArgumentNullException e)
        { Console.WriteLine("param: " + e.ParamName); }
    }
}
