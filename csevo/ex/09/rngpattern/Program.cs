// 슬라이드 p9-v8-rng-pattern — Slice(int, int) 가 있으면, C# 8.0
using System;

class Log
{
    int[] items = { 1, 2, 3, 4, 5, 6 };
    public int Count
    {
        get { Console.Write("Count "); return items.Length; }
    }
    public int Length
    {
        get { Console.Write("Length "); return items.Length; }
    }
    public int this[int i] => items[i];
    public int[] Slice(int start, int length)
    {
        Console.Write("Slice(" + start + ", " + length + ") ");
        return items.AsSpan(start, length).ToArray();
    }
}

class App
{
    static void Main()
    {
        var log = new Log();
        int[] a = log[1..4];             // start 1, length 4 - 1
        Console.WriteLine("=> " + string.Join(",", a));
        int[] b = log[^2..];             // Length is preferred
        Console.WriteLine("=> " + string.Join(",", b));
        Console.WriteLine("=> " + log[^1]);
    }
}
