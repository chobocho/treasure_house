// 슬라이드 p12-v11-lp-lower — 목록 패턴이 부르는 멤버, C# 11
using System;

class Log
{
    readonly int[] items;
    public Log(params int[] items) { this.items = items; }
    public int Count
    {
        get { Console.Write(" Count"); return items.Length; }
    }
    public int this[int i]
    {
        get { Console.Write(" [" + i + "]"); return items[i]; }
    }
}

class Program
{
    static void T(string label, Func<bool> test)
    {
        Console.Write("{0,-13}:", label);
        Console.WriteLine(" -> " + test());
    }

    static void Main()
    {
        var x = new Log(1, 2, 3);
        T("[1, .., 3]", () => x is [1, .., 3]);
        T("[1, 2, 4]", () => x is [1, 2, 4]);
        T("[..]", () => x is [..]);
        T("[_, _]", () => x is [_, _]);
        T("[.., 2, _]", () => x is [.., 2, _]);
        T("switch", () => x switch
        {
            [0, ..] => false,
            [1, ..] or [.., 1] => true,
            _ => false,
        });
    }
}
