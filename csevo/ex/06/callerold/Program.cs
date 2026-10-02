// 슬라이드 p6-v5-caller-old — 이전엔 StackFrame 으로, C# 5.0
using System;
using System.Diagnostics;
using System.Runtime.CompilerServices;

class App
{
    // Before C# 5: walk the stack at run time.
    static void Old(string msg)
    {
        StackFrame f = new StackFrame(1, true);
        Console.WriteLine("old " + msg + ": " + f.GetMethod().Name
            + " line " + f.GetFileLineNumber());
    }

    // C# 5: the compiler fills the arguments at the call site.
    static void New(string msg,
        [CallerMemberName] string member = "",
        [CallerLineNumber] int line = 0)
    {
        Console.WriteLine("new " + msg + ": " + member
            + " line " + line);
    }

    static void Main()
    {
        Old("direct");
        New("direct");
        Action a = () => Old("lambda");
        a();
        Action b = () => New("lambda");
        b();
    }
}
