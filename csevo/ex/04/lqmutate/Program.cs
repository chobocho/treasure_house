// 슬라이드 p4-v3-linq-mutate — 쿼리를 돌리며 원본을 고치면, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static void Main()
    {
        List<int> list = new List<int> { 1, 2, 3, 4 };
        try
        {
            foreach (int even in list.Where(x => x % 2 == 0))
            {
                list.Remove(even);
            }
        }
        catch (InvalidOperationException e)
        {
            Console.WriteLine(e.Message);
        }
        Console.WriteLine("after: " + string.Join(" ", list));

        list = new List<int> { 1, 2, 3, 4 };
        foreach (int even in list.Where(x => x % 2 == 0).ToList())
        {
            list.Remove(even);
        }
        Console.WriteLine("with ToList: " + string.Join(" ", list));
    }
}
