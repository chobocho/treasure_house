// 슬라이드 p15-v14-fk-hand — 아직 손으로 쓰는 필드, C# 14
using System;

class Temp
{
    double celsius;                      // shared by two properties
    public double C { get => celsius; set => celsius = value; }
    public double F
    {
        get => celsius * 9 / 5 + 32;
        set => celsius = (value - 32) * 5 / 9;
    }

    public string Label => field ??= "T=" + C;   // cached once
#if RESET
    public void Reset() => field = null;         // not an accessor
#endif
#if REF
    public ref int Slot => ref field;
#endif
}

class Program
{
    static void Main()
    {
        var t = new Temp { F = 212 };
        Console.WriteLine(t.C + " " + t.Label);
        t.C = 0;
        Console.WriteLine(t.F + " " + t.Label);
    }
}
