// 슬라이드 p7-v6-boiler5 — C# 5 로 쓴 작은 클래스, C# 5.0
using System;

class Address { public string City; }

class Person
{
    public string First, Last;
    public Address Home;

    public Person(string first, string last)
    {
        if (first == null)
            throw new ArgumentNullException("first");
        First = first;
        Last = last;
    }

    public string Describe()
    {
        string city = Home != null ? Home.City : null;
        return string.Format("{0} {1} ({2})",
            First, Last, city ?? "no address");
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
