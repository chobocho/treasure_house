// 슬라이드 p6-v5-caller-argexpr — 인수 식을 문자열로, C# 10.0
using System;
using System.Runtime.CompilerServices;

class App
{
    static void Check(bool ok,
        [CallerArgumentExpression("ok")] string expr = "")
    {
        Console.WriteLine((ok ? "ok   " : "FAIL ") + expr);
    }

    static void Main()
    {
        int x = 3;
        Check(x > 2);
        Check(x * 2 == 7);
        string name = null;
        try
        {
            // .NET's own guard methods use the same attribute.
            ArgumentNullException.ThrowIfNull(name);
        }
        catch (ArgumentNullException e)
        {
            Console.WriteLine("ParamName = " + e.ParamName);
        }
    }
}
