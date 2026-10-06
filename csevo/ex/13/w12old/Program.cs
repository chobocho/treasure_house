// 슬라이드 p13-sum-old — 같은 프로그램을 C# 11 로, C# 11.0
using System;
using System.Collections.Generic;

class Account
{
    private readonly string _owner;
    public List<int> Log;

    public Account(string owner, List<int> log)
    {
        _owner = owner;
        Log = log;
    }

    public string Owner => _owner;
    public int Total()
    {
        int t = 0;
        foreach (int x in Log) t += x;
        return t;
    }
    public static string Key => nameof(Account.Log.Count);
}

class App
{
    static void Main()
    {
        var a = new Account("ada", new List<int> { 10, 20, 30 });
        Func<int, int, int> add = (x, by) => x + by;
        (string Name, int Total) row = (a.Owner, a.Total());
        Span<int> top = stackalloc int[3];
        top[0] = add(row.Total, 1);
        int k = 5;
        Console.WriteLine($"{row.Name} {row.Total} {top[0]} "
                          + $"{Peek(in k)} {Account.Key}");

        static int Peek(in int r) => r;
    }
}
