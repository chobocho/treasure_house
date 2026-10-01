// 슬라이드 p2-v1-delnull — 빈 대리자는 null, C# 1.0
using System;

delegate void Act();

class App
{
    static void Hi() { Console.WriteLine("hi"); }

    static void Main()
    {
        Act d = null;
        d += new Act(Hi);                  // Combine(null, x) is x
        d();
        d -= new Act(Hi);                  // last one removed: null
        Console.WriteLine("null: " + (d == null));
        d();                               // calls through null
    }
}
