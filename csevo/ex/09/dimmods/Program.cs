// 슬라이드 p9-v8-dim-mods — 인터페이스 멤버의 한정자, C# 8.0
using System;

interface ICounter
{
    static int created;                    // static field: allowed
    static ICounter() => created = 100;    // static constructor

    static ICounter Make() { created++; return new Counter(); }
    static int Created => created;

    int Count { get; set; }                // abstract, as before

    void Add(int n) => Count = Clamp(Count + n);   // virtual default

    sealed void Reset() => Count = 0;      // non-virtual

    private static int Clamp(int v) => v > 9 ? 9 : v;   // helper
}

class Counter : ICounter
{
    public int Count { get; set; }
}

class App
{
    static void Main()
    {
        ICounter c = ICounter.Make();
        c.Add(5);
        c.Add(7);
        Console.WriteLine("Count " + c.Count);
        c.Reset();
        Console.WriteLine("after Reset " + c.Count);
        Console.WriteLine("Created " + ICounter.Created);
    }
}
