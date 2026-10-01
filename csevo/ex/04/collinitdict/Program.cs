// 슬라이드 p4-v3-collinit-dict — 사전 초기화자는 Add 호출, C# 3.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        Dictionary<string, int> ages = new Dictionary<string, int>
        {
            { "Ann", 31 },
            { "Bob", 25 },
        };
        Console.WriteLine(ages["Ann"] + ages["Bob"]);

        try
        {
            ages = new Dictionary<string, int>
                { { "Ann", 31 }, { "Ann", 32 } };
        }
        catch (ArgumentException e)
        {
            Console.WriteLine(e.Message);
        }
    }
}
