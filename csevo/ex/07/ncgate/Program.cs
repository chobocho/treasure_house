// 슬라이드 p7-v6-nullcond-gate — null 조건 연산자, C# 6.0
using System;

class Address { public string City; }
class Person { public string Name; public Address Home; }

class App
{
    static string CityOf5(Person p)                 // C# 5
    {
        return p != null && p.Home != null ? p.Home.City : null;
    }

    static string CityOf6(Person p)                 // C# 6
    {
        return p?.Home?.City;
    }

    static void Main()
    {
        var london = new Address { City = "London" };
        Person[] people = {
            new Person { Name = "Ada", Home = london },
            new Person { Name = "Alan" },
            null,
        };
        foreach (Person p in people)
            Console.WriteLine("[{0}] [{1}] [{2}]",
                p?.Name, CityOf5(p), CityOf6(p));
    }
}
