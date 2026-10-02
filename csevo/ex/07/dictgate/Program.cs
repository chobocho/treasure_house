// 슬라이드 p7-v6-dictinit — 인덱스 초기화자, C# 6.0
using System;
using System.Collections.Generic;

class Program
{
    static void Main()
    {
        Dictionary<int, string> errors = new Dictionary<int, string>
        {
            [404] = "Page not Found",
            [302] = "Page moved, but left a forwarding address.",
            [500] = "The web server can't come out to play today."
        };
        Console.WriteLine(errors.Count + " " + errors[404]);
    }
}
