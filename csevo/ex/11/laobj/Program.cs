// 슬라이드 p11-v10-la-obj — Delegate·object·Expression 으로, C# 10.0
using System;
using System.Linq.Expressions;

class App
{
    static int Seven() => 7;

    static void Main()
    {
        Delegate d = (string s) => s.Length;
        object o = (int x) => x + 1;
        Delegate m = Seven;
        Expression e = (string s) => s.Length;
        LambdaExpression le = (int x) => x + 1;

        Console.WriteLine(d.GetType());
        Console.WriteLine(o.GetType());
        Console.WriteLine(m.GetType());
        Console.WriteLine(e.GetType());
        Console.WriteLine(le.GetType());
        Console.WriteLine(d.DynamicInvoke("four"));
#if WARN
        object oops = Seven;          // meant Seven()?
        Console.WriteLine(oops);
#endif
    }
}
