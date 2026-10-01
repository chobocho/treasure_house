// 슬라이드 p4-v3-anon-readonly — 익명 형식의 속성은 읽기 전용, C# 3.0
using System;

class App
{
    static void Main()
    {
        var p = new { Name = "Ann", Age = 31 };
        p.Age = 32;
        Console.WriteLine(p);
    }
}
