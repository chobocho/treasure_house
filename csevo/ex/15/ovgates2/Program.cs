// 슬라이드 p15-v14-gates-demo2 — 선언에 쓰는 C# 14 기능 넷, C# 14
using System;

partial class Counter
{
    public partial event Action Changed;             // partial event
    public int Value { get; set => field = value < 0 ? 0 : value; }
    public void operator +=(int n) { Value += n; }   // compound op
}

partial class Counter
{
    Action changed;
    public partial event Action Changed
    {
        add { changed += value; }
        remove { changed -= value; }
    }
}

static class CounterExt
{
    extension<T>(T c) where T : Counter              // extensions
    {
        public bool IsZero => c.Value == 0;
    }
}

class Program
{
    static void Main()
    {
        var c = new Counter { Value = -3 };
        c += 2;
        Console.WriteLine(c.Value + " " + c.IsZero);
    }
}
