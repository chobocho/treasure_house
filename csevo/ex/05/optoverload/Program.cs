// 슬라이드 p5-v4-opt-overload — 기본값을 채워야 하는 쪽이 진다, C# 4.0
using System;

class Program
{
    static void M(int x) { Console.WriteLine("M(x)"); }
    static void M(int x, int y = 0) { Console.WriteLine("M(x, y)"); }

    static void N(int x, string s = "") { Console.WriteLine("N(s)"); }
    static void N(int x, int y = 0) { Console.WriteLine("N(y)"); }

    static void Main()
    {
        M(1);
        M(1, 2);
        N(1, "a");
        N(1, 2);
#if BAD
        N(1);
#endif
    }
}
