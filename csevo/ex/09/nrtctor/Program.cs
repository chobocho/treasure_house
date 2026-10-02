// 슬라이드 p9-v8-nrt-ctor — 생성자를 나갈 때 비어 있는 필드, C# 8.0
#nullable enable
using System;

class Person
{
    public string Name;
    public string Nick { get; set; }
    public string City = "Seoul";          // initializer: fine
    public string? Note { get; set; }      // nullable: fine

    public Person() { }                    // CS8618 twice
    public Person(string n) { Name = n; Nick = n; }
}

class App
{
    static void Main()
    {
        var p = new Person();
        Console.WriteLine(p.Name == null);
        Console.WriteLine(new Person("Ada").Nick);
    }
}
