// 슬라이드 p3-v2-anon-sort — 뺄셈으로 비교하면, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static void Print(string tag, List<int> xs)
    {
        Console.Write(tag);
        xs.ForEach(delegate(int x) { Console.Write(" " + x); });
        Console.WriteLine();
    }

    static void Main()
    {
        int[] data = new int[] { 3, int.MinValue, -1, int.MaxValue };
        List<int> a = new List<int>(data);
        List<int> b = new List<int>(data);

        a.Sort(delegate(int x, int y) { return x - y; });   // overflows
        b.Sort(delegate(int x, int y) { return x.CompareTo(y); });
        Print("x - y:    ", a);
        Print("CompareTo:", b);
    }
}
