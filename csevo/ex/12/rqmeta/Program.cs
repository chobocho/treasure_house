// 슬라이드 p12-v11-rq-meta — required 가 메타데이터에 남기는 것, C# 11
using System;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Reflection;

class Person
{
    public required string Name { get; init; }
    public Person() { }
    [SetsRequiredMembers] public Person(string n) { Name = n; }
}

class Program
{
    static void Show(string label, MemberInfo m)
    {
        Console.WriteLine(label);
        foreach (var a in m.GetCustomAttributesData())
        {
            Console.WriteLine("  [" + a.AttributeType.Name + "]");
            foreach (var arg in a.ConstructorArguments)
                Console.WriteLine("      " + arg.Value);
        }
    }

    static void Main()
    {
        Type t = typeof(Person);
        Show("class Person", t);
        Show("property Name", t.GetProperty("Name"));
        Show("Person()", t.GetConstructor(Type.EmptyTypes));
        Show("Person(string)",
            t.GetConstructor(new[] { typeof(string) }));
    }
}
