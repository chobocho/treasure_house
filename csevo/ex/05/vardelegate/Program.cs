// 슬라이드 p5-v4-var-delegate — 대리자 변수끼리의 변환, C# 4.0
using System;

class Program
{
    static string Describe(object o) { return "described " + o; }

    static void Main()
    {
        Func<object, string> f = Describe;
        Func<string, object> g = f;    // in T: object -> string
                                       // out TResult: string -> object
        Console.WriteLine(g("x"));
        Console.WriteLine(ReferenceEquals(f, g));
        Console.WriteLine(g.GetType());
    }
}
