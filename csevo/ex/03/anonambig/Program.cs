// 슬라이드 p3-v2-anon-ambig — 매개변수 없는 꼴과 오버로드, C# 2.0
using System;

delegate void NoArg();
delegate void OneArg(int x);

class App
{
    static void Run(NoArg f) { Console.WriteLine("NoArg"); f(); }
    static void Run(OneArg f) { Console.WriteLine("OneArg"); f(1); }

    static void Main()
    {
        Run(delegate(int x) { });     // only OneArg fits
        Run(delegate() { });          // only NoArg fits
        Run(delegate { });            // both fit
    }
}
