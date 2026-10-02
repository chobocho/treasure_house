// 슬라이드 p7-v6-exprbody — 식 본문 메서드, C# 6.0
using System;

class Person
{
    public string First, Last;

    public Person(string first, string last)
    {
        First = first;
        Last = last;
    }

    // the body is one expression after =>
    public override string ToString() => First + " " + Last;

    public string Initials() => First.Substring(0, 1) + Last[0];

    public static int Add(int a, int b) => a + b;
}

class Program
{
    static void Main()
    {
        Person p = new Person("Ada", "Lovelace");
        Console.WriteLine(p);
        Console.WriteLine(p.Initials());
        Console.WriteLine(Person.Add(2, 3));
    }
}
