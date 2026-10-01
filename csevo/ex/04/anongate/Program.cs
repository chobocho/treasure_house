// 슬라이드 p4-v3-anon-gate — 익명 형식, C# 3.0
using System;

class App
{
    static void Main()
    {
        object p = new { Name = "Ann", Age = 31 };
        Console.WriteLine(p);
        Console.WriteLine(new { });
    }
}
