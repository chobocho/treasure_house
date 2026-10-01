// 슬라이드 p4-v3-anon-array — 익명 형식의 배열은 new[] 로, C# 3.0
using System;

class App
{
    static void Main()
    {
        var people = new[]
        {
            new { Name = "Ann", Age = 31 },
            new { Name = "Bob", Age = 25 },
        };
        foreach (var p in people)
            Console.WriteLine(p.Name + " " + p.Age);
        Console.WriteLine(people.GetType().IsArray + " "
            + (people.GetType().GetElementType()
               == people[0].GetType()));
    }
}
