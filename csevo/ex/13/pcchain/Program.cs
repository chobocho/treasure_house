// 슬라이드 p13-v12-pc-chain — 다른 생성자는 this(…) 를 거친다, C# 12.0
using System;

class Range(int lo, int hi)
{
    public Range(int hi) : this(0, hi) { }            // OK
    public Range() : this(10)
    {
        Console.WriteLine("body runs after the chain");
    }
#if BAD
    public Range(string s) { }                         // no this(...)
#endif
    public override string ToString() => $"[{lo}, {hi})";
}

class App
{
    static void Main()
    {
        Console.WriteLine(new Range(1, 5));
        Console.WriteLine(new Range(7));
        Console.WriteLine(new Range());
    }
}
