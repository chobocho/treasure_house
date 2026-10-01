// 슬라이드 p4-v3-lambda-vsanon — 매개변수 목록 생략, C# 3.0
using System;

class App
{
    static void Main()
    {
        // an anonymous method without parameters fits any signature
        Action<int> a = delegate { Console.WriteLine("ignored"); };
        Action<string, int> b =
            delegate { Console.WriteLine("ignored too"); };
        // a lambda states the parameters, even unused ones
        Action<int> c = x => Console.WriteLine("got " + x);
        Action<string, int> d = (s, n) => Console.WriteLine(s + n);
        a(1); b("x", 2); c(3); d("y", 4);
    }
}
