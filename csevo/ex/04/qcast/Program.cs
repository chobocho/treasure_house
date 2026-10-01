// 슬라이드 p4-v3-query-cast — 범위 변수에 형식을 적으면 Cast, C# 3.0
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static void Main()
    {
        ArrayList list = new ArrayList();
        list.Add("pear");
        list.Add("fig");

        IEnumerable<string> q = from string s in list
                                orderby s
                                select s.ToUpper();
        Console.WriteLine(string.Join(" ", q));

        list.Add(42);                          // not a string
        try
        {
            Console.WriteLine(string.Join(" ", q));
        }
        catch (InvalidCastException e)
        {
            Console.WriteLine(e.GetType().Name + ": " + e.Message);
        }
    }
}
