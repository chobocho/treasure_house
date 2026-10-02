// 슬라이드 p8-v7-tuple-generic — 형식 인수 속의 이름, C# 7.0
using System;
using System.Collections.Generic;
using System.Linq;

class App
{
    static T Id<T>(T x) => x;

    static void Main()
    {
        var people = new List<(string name, int age)>
        {
            ("Kim", 30), ("Lee", 25),
        };
        var first = people.First();             // names flow through T
        Console.WriteLine(first.name);
        var same = Id(first);                   // inferred T keeps them
        Console.WriteLine(same.age);
        var young = people.Where(p => p.age < 28)
            .Select(p => (who: p.name, p.age)); // a new name, and Item2
        foreach (var y in young)
            Console.WriteLine(y.who + " " + y.Item2);
        Console.WriteLine(people.GetType().GetGenericArguments()[0]);
    }
}
