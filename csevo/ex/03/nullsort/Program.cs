// 슬라이드 p3-v2-nullable-sort — null 은 맨 앞으로 정렬된다, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        List<int?> xs = new List<int?>();
        xs.Add(3);
        xs.Add(null);
        xs.Add(-5);
        xs.Sort();                        // Comparer<int?>.Default
        foreach (int? x in xs)
        {
            Console.Write(x.HasValue ? x.Value + " " : "null ");
        }
        Console.WriteLine();
        int? n = null;
        Console.WriteLine(Nullable.Compare(n, -5) + " " + (n < -5));
    }
}
