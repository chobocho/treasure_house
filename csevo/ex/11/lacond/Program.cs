// 슬라이드 p11-v10-la-cond — 람다에 Conditional?, C# 10.0
using System;
using System.Diagnostics;

class App
{
#if LAMBDA
    static Action<string> lam = [Conditional("DEBUG")] (string s) =>
        Console.WriteLine("lambda " + s);
#endif

    [Conditional("DEBUG")]
    static void Method(string s) => Console.WriteLine("method " + s);

    static void Main()
    {
        [Conditional("DEBUG")]
        static void Local(string s) => Console.WriteLine("local " + s);

        Method("call");
        Local("call");
        Console.WriteLine("end");
    }
}
