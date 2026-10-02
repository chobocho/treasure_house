// 슬라이드 p10-v9-init-iface — 인터페이스의 init, C# 9.0
using System;

interface IPerson
{
    string Name { get; init; }
}

class Person : IPerson
{
    public string Name { get; init; }
}

class App
{
    static T Make<T>() where T : IPerson, new()
    {
        var local = new T() { Name = "Jared" };   // init through T
#if BAD
        local.Name = "Jraed";                     // Error
#endif
        return local;
    }

    static void Main()
    {
        Console.WriteLine(Make<Person>().Name);
    }
}
