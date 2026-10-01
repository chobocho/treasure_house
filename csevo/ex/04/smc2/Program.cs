// 슬라이드 p4-v3-wrap-c2 — 도시별 성인 수, C# 2.0 으로
using System;
using System.Collections.Generic;

class Person
{
    string name, city;
    int age;
    public Person(string name, string city, int age)
    {
        this.name = name; this.city = city; this.age = age;
    }
    public string Name { get { return name; } }
    public string City { get { return city; } }
    public int Age { get { return age; } }
}

class Program
{
    static void Main()
    {
        List<Person> people = new List<Person>();
        people.Add(new Person("Kim", "Seoul", 34));
        people.Add(new Person("Lee", "Busan", 17));
        people.Add(new Person("Park", "Seoul", 41));
        people.Add(new Person("Choi", "Daegu", 25));
        people.Add(new Person("Jung", "Busan", 30));

        Dictionary<string, int> counts = new Dictionary<string, int>();
        List<string> cities = new List<string>();
        foreach (Person p in people)
        {
            if (p.Age < 18) continue;
            if (!counts.ContainsKey(p.City))
            {
                counts[p.City] = 0;
                cities.Add(p.City);
            }
            counts[p.City]++;
        }
        cities.Sort(delegate(string a, string b)
        {
            int c = counts[b].CompareTo(counts[a]);
            return c != 0 ? c : string.CompareOrdinal(a, b);
        });
        foreach (string city in cities)
        {
            Console.WriteLine(city + ": " + counts[city]);
        }
    }
}
