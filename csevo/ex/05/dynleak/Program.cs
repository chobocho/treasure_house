// 슬라이드 p5-v4-dyn-leak — dynamic 은 번진다, C# 4.0
using System;
using Microsoft.CSharp.RuntimeBinder;

class Program
{
    static void Main()
    {
        dynamic d = "hello";
        var n = d.Length;       // n is dynamic, not int
        int m = d.Length;       // m is int
        Console.WriteLine(n + m);
        try
        {
            string s = n;       // compiles: n is dynamic
            Console.WriteLine(s);
        }
        catch (RuntimeBinderException e)
        {
            Console.WriteLine(e.Message);
        }
#if BAD
        string t = m;           // m is int: a compile-time error
#endif
    }
}
