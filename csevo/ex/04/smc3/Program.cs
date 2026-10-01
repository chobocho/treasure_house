// 슬라이드 p4-v3-wrap-c3 — 도시별 성인 수, C# 3.0 으로
using System;
using System.Collections.Generic;
using System.Linq;

class Person
{
    public string Name { get; set; }
    public string City { get; set; }
    public int Age { get; set; }
}

class Program
{
    static void Main()
    {
        var people = new List<Person> {
            new Person { Name = "Kim", City = "Seoul", Age = 34 },
            new Person { Name = "Lee", City = "Busan", Age = 17 },
            new Person { Name = "Park", City = "Seoul", Age = 41 },
            new Person { Name = "Choi", City = "Daegu", Age = 25 },
            new Person { Name = "Jung", City = "Busan", Age = 30 },
        };

        var counts = from p in people
                     where p.Age >= 18
                     group p by p.City into g
                     orderby g.Count() descending, g.Key
                     select new { City = g.Key, Count = g.Count() };

        foreach (var c in counts)
        {
            Console.WriteLine(c.City + ": " + c.Count);
        }
    }
}
