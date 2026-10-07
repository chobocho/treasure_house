// 슬라이드 p15-v14-xm-logic — 확장 &·true·false 로 쓰는 &&, C# 14
using System;

class Bits { public bool On; public Bits(bool on) { On = on; } }

static class BitOps
{
    extension(Bits)
    {
        public static Bits operator &(Bits a, Bits b) =>
            new(a.On && b.On);
        public static bool operator true(Bits b) => b.On;
        public static bool operator false(Bits b) => !b.On;
    }

    extension(Bits)                        // the pair in another block
    {
        public static bool operator <(Bits a, Bits b) => !a.On && b.On;
        public static bool operator >(Bits a, Bits b) => a.On && !b.On;
    }
}

class Program
{
    static Bits Trace(string s)
    {
        Console.Write(s + " ");
        return new(true);
    }

    static void Main()
    {
        Bits t = new(true), f = new(false);
        Console.WriteLine((f && Trace("right")).On);   // short-circuit
        Console.WriteLine((t && Trace("right")).On);
        Console.WriteLine((f < t) + " " + (t > f));
    }
}
