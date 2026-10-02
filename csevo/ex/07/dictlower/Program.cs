// 슬라이드 p7-v6-dictinit-lower — Add 와 인덱서 대입, C# 6.0
using System;
using System.Collections;
using System.Collections.Generic;

class Spy : IEnumerable
{
    public void Add(string k, int v)
    {
        Console.WriteLine("  Add(" + k + ", " + v + ")");
    }
    public int this[string k]
    {
        set { Console.WriteLine("  this[" + k + "] = " + value); }
    }

    public IEnumerator GetEnumerator() { return null; }
}

class Program
{
    static void Main()
    {
        Console.WriteLine("{ k, v }:");
        new Spy { { "a", 1 }, { "a", 2 } };
        Console.WriteLine("[k] = v:");
        new Spy { ["a"] = 1, ["a"] = 2 };

        var d = new Dictionary<string, int> { ["a"] = 1, ["a"] = 2 };
        Console.WriteLine("indexer: a = " + d["a"]);
        try
        {
            new Dictionary<string, int> { { "a", 1 }, { "a", 2 } };
        }
        catch (ArgumentException e)
        {
            Console.WriteLine("Add: " + e.GetType().Name);
        }
    }
}
