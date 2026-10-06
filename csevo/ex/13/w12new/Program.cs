// 슬라이드 p13-sum-new — 같은 프로그램을 C# 12 로, C# 12.0
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using Row = (string Name, int Total);         // alias any type

class Account(string owner, List<int> log)    // primary constructor
{
    public List<int> Log = log;

    public string Owner => owner;
    public int Total()
    {
        int t = 0;
        foreach (int x in Log) t += x;
        return t;
    }
    public static string Key => nameof(Log.Count);   // nameof
}

[InlineArray(3)] struct Top3 { int _e; }      // inline array

class App
{
    static void Main()
    {
        var a = new Account("ada", [10, 20, 30]);    // collection expr
        var add = (int x, int by = 1) => x + by;     // default lambda
        Row row = (a.Owner, a.Total());
        var top = new Top3();
        top[0] = add(row.Total);
        int k = 5;
        Console.WriteLine($"{row.Name} {row.Total} {top[0]} "
                          + $"{Peek(in k)} {Account.Key}");

        static int Peek(ref readonly int r) => r;    // ref readonly
    }
}
