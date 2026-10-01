// 슬라이드 p4-v3-wrap-methods — 같은 쿼리를 메서드 호출로, C# 3.0
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

        var counts = people
            .Where(p => p.Age >= 18)
            .GroupBy(p => p.City)
            .OrderByDescending(g => g.Count())
            .ThenBy(g => g.Key)
            .Select(g => new { City = g.Key, Count = g.Count() });

        foreach (var c in counts)
        {
            Console.WriteLine(c.City + ": " + c.Count);
        }
    }
}
