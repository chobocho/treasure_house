// 슬라이드 p7-v6-immut-required — required 와 init, C# 11.0
using System;

class P
{
    public required string Name { get; init; }
    public int Age { get; init; }
}

class App
{
    static void Main()
    {
        P p = new P { Name = "Ada", Age = 36 };
        Console.WriteLine(p.Name + " " + p.Age);
#if BAD
        P q = new P { Age = 1 };
#endif
    }
}
