// 슬라이드 p14-v13-field — field 키워드(C# 13 의 미리 보기), C# 14
using System;

class Person
{
    public string Name
    {
        get;
        set => field = value?.Trim()
            ?? throw new ArgumentNullException(nameof(value));
    }

    public int Visits { get => field++; }   // backing field, no name
}

class Program
{
    static void Main()
    {
        var p = new Person { Name = "  Ada " };
        Console.WriteLine("[" + p.Name + "]");
        Console.WriteLine(p.Visits + " " + p.Visits + " " + p.Visits);
        foreach (var f in typeof(Person).GetFields(
                     System.Reflection.BindingFlags.NonPublic
                     | System.Reflection.BindingFlags.Instance))
            Console.WriteLine(f.Name);
    }
}
