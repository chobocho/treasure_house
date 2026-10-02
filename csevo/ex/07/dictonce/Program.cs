// 슬라이드 p7-v6-dictinit-once — 인덱서 인자는 한 번만, C# 6.0
using System;
using System.Collections.Generic;

class Shelf
{
    List<int>[] rows = { new List<int>(), new List<int>() };

    public List<int> this[int i]
    {
        get
        {
            Console.WriteLine("  get this[" + i + "]");
            return rows[i];
        }
    }
}

class Program
{
    static int Key(int i)
    {
        Console.WriteLine("  Key(" + i + ")");
        return i;
    }

    static void Main()
    {
        Shelf s = new Shelf { [Key(0)] = { 1, 2, 3 }, [Key(1)] = { } };
        Console.WriteLine(s[0].Count + " " + s[1].Count);
    }
}
