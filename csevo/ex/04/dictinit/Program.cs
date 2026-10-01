// 슬라이드 p4-v3-collinit-later — 인덱서 초기화자, C# 6
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        Dictionary<string, int> ages = new Dictionary<string, int>
        {
            ["Ann"] = 31,
            ["Ann"] = 32,      // indexer: overwrites, no exception
        };
        Console.WriteLine(ages.Count + " " + ages["Ann"]);
    }
}
