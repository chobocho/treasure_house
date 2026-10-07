// 슬라이드 p15-v14-na-compound — 복합 대입과 ??=, C# 14
using System;

class Counter
{
    public int Hits;
    public string Label;
}

class Program
{
    static int Step(int n)
    {
        Console.WriteLine("  Step(" + n + ")");
        return n;
    }

    static void Main()
    {
        Counter on = new Counter(), off = null;
        on?.Hits += Step(3);
        off?.Hits += Step(4);          // Step(4) is not called
        on?.Hits *= 2;
        on?.Label ??= "first";
        on?.Label ??= "second";        // already set: unchanged
        off?.Label ??= "never";
        Console.WriteLine(on.Hits + " " + on.Label);
#if INC
        on?.Hits++;
#endif
#if PREDEC
        --on?.Hits;
#endif
    }
}
