// 슬라이드 p3-v2-mg-overload — 오버로드끼리 만나면, C# 2.0
using System;

delegate void IntSink(int x);
delegate void StrSink(string s);

class App
{
    static void Show(int x) { }
    static void Show(string s) { }

    static void Run(IntSink f) { f(1); }
    static void Run(StrSink f) { f("one"); }

    static void Main()
    {
        Run(Show);                       // Show fits both Run
        Run(new IntSink(Show));          // say which one
    }
}
