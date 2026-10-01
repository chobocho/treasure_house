// 슬라이드 p4-v3-linq-join — Join 은 안쪽을 먼저 다 읽는다, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static IEnumerable<int> Src(string name, int[] xs)
    {
        foreach (int x in xs)
        {
            Console.WriteLine("  " + name + " " + x);
            yield return x;
        }
    }

    static void Main()
    {
        IEnumerable<int> outer = Src("outer", new int[] { 1, 2, 3 });
        IEnumerable<int> inner = Src("inner", new int[] { 3, 1 });

        IEnumerable<string> q = from o in outer
                                join i in inner on o equals i
                                select "match " + o;
        foreach (string s in q)
        {
            Console.WriteLine(s);
        }
    }
}
