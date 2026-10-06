// 슬라이드 p13-v12-nameof — nameof 안의 인스턴스 멤버, C# 12.0
using System;

class Person
{
    public string Name = "";
    public Person Boss;

    // static field initializer: no instance exists here
    static readonly string Key = nameof(Boss.Name.Length);

    public static string Describe() =>
        nameof(Name.ToUpper) + " " + nameof(Boss.Boss) + " " + Key;
}

class App
{
    static void Main()
    {
        Console.WriteLine(Person.Describe());
        var p = new Person { Boss = new Person() };
        Console.WriteLine(p.Boss.Name.Length);
    }
}
