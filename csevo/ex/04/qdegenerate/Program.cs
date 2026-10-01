// 슬라이드 p4-v3-query-degenerate — 원본을 돌려주지 않는 쿼리, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Leaky
{
    int[] items = { 1, 2, 3 };
    public IEnumerable<int> Items { get { return items; } }
    public int First { get { return items[0]; } }
}

class Safe
{
    int[] items = { 1, 2, 3 };
    public IEnumerable<int> Items
    {
        get { return from x in items select x; }
    }
    public int First { get { return items[0]; } }
}

class Program
{
    static void Main()
    {
        Leaky leaky = new Leaky();
        int[] a = leaky.Items as int[];
        if (a != null) a[0] = 99;
        Console.WriteLine("Leaky: " + leaky.First);

        Safe safe = new Safe();
        int[] b = safe.Items as int[];
        if (b != null) b[0] = 99;
        Console.WriteLine("Safe:  " + safe.First + " (cast null: "
                          + (b == null) + ")");
    }
}
