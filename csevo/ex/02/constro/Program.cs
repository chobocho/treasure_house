// 슬라이드 p2-v1-const — const 와 readonly, C# 1.0
using System;
using System.Collections;

class Config
{
    public const int Max = 3;                 // compile-time, static
    public const string Name = "csevo";
    public static readonly int[] Primes = { 2, 3, 5 }; // not const
    public readonly int Id;                   // set once, at run time
    public readonly ArrayList Items = new ArrayList();

    public Config(int id)
    {
        Id = id;                              // only in a constructor
    }
}

class App
{
    const int Twice = Config.Max * 2;         // consts compose

    static void Main()
    {
        Config c = new Config(7);
        Console.WriteLine(Config.Max + " " + Config.Name + " " + Twice);
        Console.WriteLine(Config.Primes.Length);
        Console.WriteLine(c.Id);
        c.Items.Add("still mutable");         // the list itself is not
        Console.WriteLine(c.Items.Count);
    }
}
