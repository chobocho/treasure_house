// 슬라이드 p4-v3-var-gate — 암시적 형식 지역 변수 var, C# 3.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        var n = 5;
        var s = "five";
        var map = new Dictionary<string, List<int>>();
        map[s] = new List<int>();
        map[s].Add(n);
        Console.WriteLine(n.GetType() + " " + s.GetType());
        Console.WriteLine(map.GetType().Name + " " + map[s].Count);
    }
}
