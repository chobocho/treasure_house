// 슬라이드 p13-v12-pc-double-base — 기반에 넘기고 포착도, C# 12.0
using System;

class Named(string name)
{
    public string Name { get; set; } = name;
}

class Employee(string name, int no) : Named(name)
{
    public string Badge => $"{no}:{name}";       // captured again
}

class App
{
    static void Main()
    {
        var e = new Employee("Kim", 7);
        e.Name = "Lee";
        Console.WriteLine($"Name={e.Name} Badge={e.Badge}");
    }
}
