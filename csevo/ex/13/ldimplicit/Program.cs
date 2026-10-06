// 슬라이드 p13-v12-ld-implicit — 기본값을 못 쓰는 두 자리, C# 12
using System;

delegate int M1(int i = 3);

class Program
{
    static void Main()
    {
        M1 m = (int x) => x + x;        // typed: takes M1's default
        Console.WriteLine(m());
#if BAD
        M1 bad = (x = 3) => x + x;
#endif
#if BAD2
        Func<int, int> anon = delegate (int x = 1) { return x; };
#endif
    }
}
