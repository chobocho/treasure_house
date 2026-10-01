// 슬라이드 p4-v3-gates — C# 3 의 여덟 조각을 한 파일에, C# 3.0
using System;
using System.Collections.Generic;

static class Ext
{
    public static int Twice(this int x) { return x * 2; }
}

partial class Person
{
    public string Name { get; set; }
    public int Age { get; set; }
    partial void OnCreated();
}

class App
{
    static void Main()
    {
        var people = new List<Person>
        {
            new Person { Name = "Ann", Age = 31 },
            new Person { Name = "Bob", Age = 25 }
        };
        Func<Person, bool> young = p => p.Age < 30;
        foreach (var p in people)
        {
            if (young(p)) continue;
            var card = new { p.Name, Double = p.Age.Twice() };
            Console.WriteLine(card);
        }
        var sizes = new[] { 1, 2, 3 };
        Console.WriteLine(sizes.Length);
    }
}
