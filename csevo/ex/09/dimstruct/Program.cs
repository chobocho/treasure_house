// 슬라이드 p9-v8-dim-struct — 구조체와 기본 구현, C# 8.0
using System;

interface IB
{
    int P { get; set; }
    void Increment() { P += 1; }
}

struct T : IB
{
    public int P { get; set; }
}

class App
{
    static void Main()
    {
        T t = default(T);
        Console.WriteLine(t.P);            // 0
        (t as IB).Increment();             // boxes a copy of t
        Console.WriteLine(t.P);            // still 0

        IB boxed = t;                      // one box, kept
        boxed.Increment();
        boxed.Increment();
        Console.WriteLine(boxed.P + " " + t.P);
    }
}
