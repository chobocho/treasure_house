// 슬라이드 p3-v2-mg-overload — 오버로드 가운데 대리자에 맞는 것, C# 2.0
using System;

delegate void IntSink(int x);
delegate void StrSink(string s);

class App
{
    static void Show(int x) { Console.WriteLine("int " + x); }
    static void Show(string s) { Console.WriteLine("string " + s); }

    static void Main()
    {
        IntSink a = Show;                // picks Show(int)
        StrSink b = Show;                // picks Show(string)
        a(1);
        b("one");
        Console.WriteLine(a.Method.GetParameters()[0].ParameterType);
    }
}
