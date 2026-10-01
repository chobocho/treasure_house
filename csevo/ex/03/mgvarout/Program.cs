// 슬라이드 p3-v2-variance-later — 대리자 형식의 변성 선언, C# 4.0
using System;

delegate T Maker<out T>();               // out: C# 4

class App
{
    static string MakeS() { return "made"; }

    static void Main()
    {
        Maker<string> ms = MakeS;
        Maker<object> mo = ms;            // now a conversion exists
        Console.WriteLine(mo() + " " + object.ReferenceEquals(mo, ms));
    }
}
