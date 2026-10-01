// 슬라이드 p3-v2-fixed-later — 안전한 후계자 인라인 배열, C# 12
using System;
using System.Runtime.CompilerServices;

[InlineArray(4)]
struct Buf4 { int first; }               // 4 ints inline, no unsafe

class App
{
    static void Main()
    {
        Buf4 b = new Buf4();
        b[0] = 1;
        b[3] = 4;
        Console.WriteLine(b[0] + " " + b[3]);
        try
        {
            int i = 4;
            b[i] = 99;                       // checked
        }
        catch (IndexOutOfRangeException e)
        {
            Console.WriteLine(e.GetType().Name);
        }
    }
}
