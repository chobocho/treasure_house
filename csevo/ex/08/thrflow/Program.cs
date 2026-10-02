// 슬라이드 p8-v7-throw-flow — throw 식과 확정 대입, C# 7.0
using System;

class App
{
    static int Parse(string s)
    {
        int n;
        bool ok = int.TryParse(s, out n)
            ? n >= 0
            : throw new FormatException("bad: " + s);
        return ok ? n : -n;
    }

    static void Main(string[] args)
    {
        int x;
        bool flag = args.Length == 0;
        int y = flag ? (x = 1) : throw new Exception();
        Console.WriteLine(x + y);   // x is definitely assigned
        Console.WriteLine(Parse("-5"));
#if BAD
        int z;
        int w = flag ? (z = 1) : 0;
        Console.WriteLine(z);       // the 0 branch leaves z unassigned
#endif
    }
}
