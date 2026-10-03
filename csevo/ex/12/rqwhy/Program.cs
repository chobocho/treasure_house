// 슬라이드 p12-v11-rq-why — 생성자로만 강제하던 시절, C# 10
using System;

class Person
{
    public string First { get; }
    public string Last { get; }
    public Person(string first, string last)
    { First = first; Last = last; }
}

class Student : Person          // repeats every parameter
{
    public int Id { get; }
    public Student(string first, string last, int id)
        : base(first, last) { Id = id; }
}

class Person2                   // C# 9 init: nothing forces Last
{
    public string First { get; init; }
    public string Last { get; init; }
}

class Program
{
    static void Main()
    {
        var s = new Student("Ada", "Lovelace", 1);
        Console.WriteLine(s.First + " " + s.Last + " #" + s.Id);
        var p = new Person2 { First = "Ada" };
        Console.WriteLine(p.Last ?? "(Last is null)");
    }
}
