// 슬라이드 p4-v3-anon-with — 익명 형식에 with 식, C# 10
using System;

class App
{
    static void Main()
    {
        var a = new { Name = "Ann", Age = 31 };
        var b = a with { Age = 32 };
        Console.WriteLine(a);
        Console.WriteLine(b);
    }
}
