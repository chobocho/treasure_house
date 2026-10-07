// 슬라이드 p15-v14-field — field 키워드, C# 14
using System;

class Customer
{
    public string Email
    {
        get;
        set => field = value?.Trim() ?? "";
    }
}

class Program
{
    static void Main()
    {
        var c = new Customer();
        Console.WriteLine(c.Email ?? "null");
        c.Email = "  ada@example.com ";
        Console.WriteLine("[" + c.Email + "]");
        c.Email = null;
        Console.WriteLine("[" + c.Email + "]");
    }
}
