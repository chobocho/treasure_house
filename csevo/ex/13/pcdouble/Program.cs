// 슬라이드 p13-v12-pc-double — 같은 값을 두 번 저장하는 경고, C# 12.0
using System;

class Person(string name)
{
    public string Name { get; set; } = name;     // stored once...
    public override string ToString() => name;   // ...and captured
}

class App
{
    static void Main()
    {
        var p = new Person("Kim");
        p.Name = "Lee";
        Console.WriteLine($"Name={p.Name} ToString={p}");
    }
}
