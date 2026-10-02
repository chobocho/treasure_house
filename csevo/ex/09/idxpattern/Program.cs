// 슬라이드 p9-v8-idx-pattern — Length 와 this[int] 만 있으면, C# 8.0
using System;

class Ring                         // knows nothing about Index
{
    int[] items = { 10, 20, 30, 40 };
    public int Length
    {
        get { Console.Write("Length "); return items.Length; }
    }
    public int this[int i]
    {
        get { Console.Write("this[" + i + "] "); return items[i]; }
    }
}

class App
{
    static Ring Get()
    {
        Console.Write("Get ");
        return new Ring();
    }

    static void Main()
    {
        Console.WriteLine("=> " + Get()[^1]);
        Index i = ^2;                    // not a literal ^n
        Console.WriteLine("=> " + Get()[i]);
        Console.WriteLine("=> " + Get()[1]);
    }
}
