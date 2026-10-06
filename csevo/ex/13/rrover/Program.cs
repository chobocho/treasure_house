// 슬라이드 p13-v12-rr-over — 값 오버로드와 ref readonly, C# 12.0
using System;

interface I1 { }
interface I2 { }

class App
{
    static string V(int i) => "value";
    static string V(ref readonly int i) => "rr";

    static string M(I1 o, in int i) => "1";
    static string M(I2 o, ref readonly int i) => "2";

    static void Main()
    {
        int i = 5;
        Console.WriteLine(V(i) + " " + V(in i) + " " + V(ref i));
#if BAD
        Console.WriteLine(M(null, ref i));
#elif BAD2
        Console.WriteLine(M(null, in i));
#elif BAD3
        Console.WriteLine(M(null, i));
#endif
    }
}
