// 슬라이드 p13-v12-rr-calls — 부르는 쪽 수식어와 매개변수, C# 12.0
using System;

class App
{
    static int Ref(ref int p) => p;
    static int RR(ref readonly int p) => p;
    static int In(in int p) => p;
    static readonly int Ro = 2;

    static void Main()
    {
        int x = 1;
        // the cases that need no diagnostic at all
        int s = Ref(ref x) + RR(ref x) + RR(in x) + RR(in Ro)
              + In(in x) + In(x) + In(5);
        Console.WriteLine(s);
#if A1
        s += In(ref x);            // ref -> in: was an error
#elif A2
        s += RR(out x);            // out -> ref readonly
#elif A3
        s += Ref(in x);            // in -> ref
#elif A4
        s += RR(in 5);             // in with a value
#elif A5
        s += RR(ref Ro);           // ref to a readonly field
#endif
    }
}
