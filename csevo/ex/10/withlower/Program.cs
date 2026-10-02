// 슬라이드 p10-v9-with-lower — with 가 부르는 것, C# 9.0
using System;

record Box
{
    int a, b;
    public int A
    {
        get => a;
        init { Console.WriteLine("init A=" + value); a = value; }
    }
    public int B
    {
        get => b;
        init { Console.WriteLine("init B=" + value); b = value; }
    }

    public Box() { }
    protected Box(Box original)              // our copy constructor
    {
        Console.WriteLine("copy ctor");
        a = original.a;
        b = original.b;
    }
}

class App
{
    static void Main()
    {
        var x = new Box { A = 1, B = 2 };
        Console.WriteLine("--- with");
        var y = x with { B = 20, A = 10 };   // lexical order
        Console.WriteLine(y);
    }
}
