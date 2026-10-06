// 슬라이드 p14-v13-pp-gen — 사람이 쓰는 조각, C# 13.0
using System;

[AttributeUsage(AttributeTargets.Property)]
class NotifyAttribute : Attribute { }

// the user declares; a generator would implement (see Gen.cs)
partial class Person
{
    [Notify] public partial string Name { get; set; }
    [Notify] public partial int Age { get; set; }
}

class App
{
    static void Main()
    {
        var p = new Person();
        p.Changed += what => Console.WriteLine("changed: " + what);
        p.Name = "Kim";
        p.Age = 30;
        p.Age = 30;                    // same value: no event
        Console.WriteLine(p.Name + " " + p.Age);
    }
}
