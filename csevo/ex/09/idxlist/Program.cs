// 슬라이드 p9-v8-idx-list — List<T> 와 ^·.., C# 8.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        var list = new List<int> { 1, 2, 3, 4, 5 };
        Console.WriteLine(list[^1]);             // list[list.Count - 1]
        list[^1] = 50;                           // the setter works too

        // on .NET 10, List<T> has Slice(int, int): ranges bind to it
        List<int> part = list[1..3];
        part[0] = 99;
        Console.WriteLine("part {0}, list {1}",
            string.Join(",", part), string.Join(",", list));

        var m = typeof(List<int>).GetMethod("Slice");
        Console.WriteLine(m);
    }
}
