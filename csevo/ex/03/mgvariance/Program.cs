// 슬라이드 p3-v2-delegate-variance — 메서드 그룹의 공변·반공변, C# 2.0
using System;

delegate string D1(object o);
delegate object D2(string s);

class App
{
    static string F(object o) { return "F(" + o + ")"; }

    static void Main()
    {
        D1 d1 = F;                       // exact match
        D2 d2 = F;                       // param: string -> object
                                         // return: string -> object
        D2 d3 = new D2(F);               // the same with the C# 1 form
        Console.WriteLine(d1(42));
        Console.WriteLine(d2("s"));
        Console.WriteLine(d3("t"));
    }
}
