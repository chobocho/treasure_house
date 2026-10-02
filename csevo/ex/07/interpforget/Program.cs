// 슬라이드 p7-v6-interp-forget — $ 를 빠뜨리면, C# 6.0
using System;

class App
{
    static void Main()
    {
        string name = "Ada";
        Console.WriteLine("Hello, {name}!");     // no $: plain text
        Console.WriteLine($"Hello, {name}!");
        // a format string built by interpolation, then formatted again
        string user = "{0}";
        string msg = $"user {user} logged in";
        Console.WriteLine(msg);
        try
        {
            Console.WriteLine(msg, "!");      // WriteLine(format, arg)
            Console.WriteLine(string.Format($"{{{name}}}", 1));
        }
        catch (FormatException e)
        {
            Console.WriteLine("FormatException: " + e.Message);
        }
    }
}
