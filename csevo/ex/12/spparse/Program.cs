// 슬라이드 p12-v11-spanpat-parse — 잘라 낸 조각을 바로 switch, C# 11.0
using System;

class App
{
    static int Eval(ReadOnlySpan<char> src)
    {
        int acc = 0;
        while (!src.IsEmpty)
        {
            int sp = src.IndexOf(' ');
            ReadOnlySpan<char> tok = sp < 0 ? src : src[..sp];
            src = sp < 0 ? default : src[(sp + 1)..];
            acc = tok switch
            {
                "inc" => acc + 1,
                "dbl" => acc * 2,
                "neg" => -acc,
                "zero" => 0,
                _ => throw new FormatException(tok.ToString()),
            };
        }
        return acc;
    }

    static void Main()
    {
        Console.WriteLine(Eval("inc inc dbl neg"));
        long before = GC.GetAllocatedBytesForCurrentThread();
        int r = Eval("zero inc dbl dbl dbl");
        long after = GC.GetAllocatedBytesForCurrentThread();
        Console.WriteLine($"{r}, allocated nothing: {after == before}");
    }
}
