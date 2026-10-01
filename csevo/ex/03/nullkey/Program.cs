// 슬라이드 p3-v2-nullable-key — null 은 사전의 열쇠가 못 된다, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        Dictionary<int?, string> d = new Dictionary<int?, string>();
        d[1] = "one";
        Console.WriteLine(d.ContainsKey(1));
        try
        {
            d[null] = "none";
        }
        catch (ArgumentNullException e)
        {
            Console.WriteLine(e.GetType().Name + " " + e.ParamName);
        }
        List<int?> list = new List<int?>();
        list.Add(null);                   // a list is fine with null
        Console.WriteLine(list.Contains(null));
    }
}
