// 슬라이드 p4-v3-linq-source — 쿼리는 원본을 복사하지 않는다, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static void Main()
    {
        List<string> names = new List<string> { "Kim", "Lee" };
        IEnumerable<string> q = names.Where(n => n.Length == 3);

        names.Add("Ahn");
        names.Remove("Kim");
        Console.WriteLine("live: " + string.Join(" ", q));

        string[] snap = q.ToArray();
        names.Add("Cho");
        Console.WriteLine("live: " + string.Join(" ", q));
        Console.WriteLine("snap: " + string.Join(" ", snap));
    }
}
