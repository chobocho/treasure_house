// 슬라이드 p5-v4-dyn-index — 인덱서·속성·foreach, C# 4.0
using System;
using System.Collections.Generic;

class Program
{
    static void Main()
    {
        dynamic list = new List<int>();
        list.Add(10);
        list.Add(20);
        dynamic arr = new string[] { "a", "b" };
        dynamic map = new Dictionary<string, int>();
        map["x"] = 1;

        Console.WriteLine(list[1] + list.Count);
        Console.WriteLine(arr[0] + arr.Length);
        Console.WriteLine(map["x"] + map.Count);

        foreach (dynamic item in list)    // dynamic -> IEnumerable
        {
            Console.WriteLine(item * 2);
        }
        arr[1] = 3;                       // string[] gets an int?
    }
}
