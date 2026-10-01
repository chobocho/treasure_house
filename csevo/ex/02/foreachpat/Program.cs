// 슬라이드 p2-v1-foreachpat — 인터페이스 없이도 foreach, C# 1.0
using System;

class Countdown                          // implements no interface
{
    int from;
    public Countdown(int from) { this.from = from; }
    public Enumerator GetEnumerator() { return new Enumerator(from); }

    public class Enumerator              // nor does this
    {
        int cur;
        public Enumerator(int from) { cur = from + 1; }
        public bool MoveNext() { return --cur > 0; }
        public int Current { get { return cur; } }   // typed: no cast
    }
}

class App
{
    static void Main()
    {
        foreach (int n in new Countdown(3))
            Console.Write(n + " ");
        Console.WriteLine();
        Console.WriteLine("interfaces: "
            + typeof(Countdown).GetInterfaces().Length);
    }
}
