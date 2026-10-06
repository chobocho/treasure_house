// 슬라이드 p13-v12-ia-index — 인덱스·범위·범위 밖, C# 12.0
using System;
using System.Runtime.CompilerServices;

[InlineArray(8)] struct Buf { int _e; }

class App
{
    static void Main()
    {
        var b = new Buf();
        for (int i = 0; i < 8; i++) b[i] = i * 10;
        Console.WriteLine(b[^1] + " " + b[^8]);     // Index
        Span<int> mid = b[2..5];                    // Range -> Span
        mid[0] = -1;
        Console.WriteLine(b[2] + " " + mid.Length);
        int k = 8;
        try
        {
            b[k] = 1;                               // run-time check
        }
        catch (IndexOutOfRangeException e)
        {
            Console.WriteLine(e.GetType().Name);
        }
#if BAD
        b[8] = 1;                  // constant index: compile time
#elif BAD2
        Span<int> t = b[6..9];     // constant range past the end
#endif
    }
}
