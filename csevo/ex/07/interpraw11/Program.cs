// 슬라이드 p7-v6-interp-raw11 — 원시 보간 문자열, C# 11.0
using System;

class App
{
    static void Main()
    {
        string name = "Ada";
        int age = 36;
        Console.WriteLine($"""
            {name} said "hi" at {age}
            """);
        Console.WriteLine($$"""
            { "name": "{{name}}", "age": {{age}} }
            """);
    }
}
