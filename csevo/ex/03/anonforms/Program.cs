// 슬라이드 p3-v2-anon-forms — 익명 메서드의 꼴, C# 2.0
using System;

delegate int Op(int a, int b);
delegate void Log(string msg);

class App
{
    static int Apply(Op f) { return f(6, 3); }

    static void Main()
    {
        Op add = delegate(int a, int b) { return a + b; };
        Log log = delegate(string m) { Console.WriteLine("log " + m); };
        Log quiet = delegate { };              // no parameter list
        EventHandler h = delegate { Console.WriteLine("event"); };

        log("add " + add(2, 5));
        quiet("ignored");
        h(null, EventArgs.Empty);
        Console.WriteLine(
            Apply(delegate(int a, int b) { return a * b; }));
    }
}
