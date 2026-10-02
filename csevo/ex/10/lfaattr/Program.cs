// 슬라이드 p10-v9-locfn-attr — 지역 함수의 특성, C# 9.0
using System;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;

class App
{
    static void Main(string[] args)
    {
        string? s = args.Length > 0 ? args[0] : "text";
        if (IsSet(s))
            Console.WriteLine(s.Length);         // no CS8602
        Log("hello");                            // erased without DEBUG
        Console.WriteLine("done");

        static bool IsSet([NotNullWhen(true)] string? v) => v != null;

        [Conditional("DEBUG")]
        static void Log(string m) => Console.WriteLine("log: " + m);
#if BAD
        [Conditional("DEBUG")]
        void Trace(string m) => Console.WriteLine(m);    // not static
        Trace(s);
#endif
    }
}
