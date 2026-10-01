// 슬라이드 p3-v2-variance-vs-type — 대리자 형식 사이의 변환, C# 2.0
using System;

delegate T Maker<T>();

class App
{
    static string MakeS() { return "made"; }

    static void Main()
    {
        Maker<string> ms = MakeS;
        Maker<object> mo = ms;                  // no conversion
        Maker<object> m2 = new Maker<object>(ms);   // ok
    }
}
