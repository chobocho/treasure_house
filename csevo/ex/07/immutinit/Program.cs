// 슬라이드 p7-v6-immut-init — { get; } 와 init, C# 9.0
using System;

class Person
{
    public string Name { get; init; }    // C# 9
    public int Age { get; }              // C# 6

    public Person(int age)
    {
        Age = age;
    }
}

class Program
{
    static void Main()
    {
        Person p = new Person(36) { Name = "Ada" };
        Console.WriteLine(p.Name + " " + p.Age);
#if BAD
        Person q = new Person(1) { Age = 2 };
        p.Name = "Bob";
#endif
    }
}
