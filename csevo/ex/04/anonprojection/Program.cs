// 슬라이드 p4-v3-anon-projection — 투영 초기화자, C# 3.0
using System;

class Person
{
    public string Name;
    public int Age;
}

class App
{
    static void Main()
    {
        Person p = new Person();
        p.Name = "Ann";
        p.Age = 31;
        int rank = 2;

        var a = new { p.Name, p.Age, rank };            // projections
        var b = new { Name = p.Name, Age = p.Age, rank = rank };
        var c = new { p.Name.Length, Upper = p.Name.ToUpper() };
        Console.WriteLine(a);
        Console.WriteLine(a.GetType() == b.GetType());
        Console.WriteLine(c);
    }
}
