// 슬라이드 p5-v4-dyn-binderex — 실행 중 바인딩의 실패, C# 4.0
using System;
using Microsoft.CSharp.RuntimeBinder;

class Secret
{
    private void Hidden() { }
    public void Touch() { Hidden(); }
}

class Program
{
    delegate void Act();

    static void Try(string label, Act act)
    {
        try { act(); }
        catch (RuntimeBinderException e)
        {
            Console.WriteLine(label + ":\n  " + e.Message);
        }
    }

    static void Main()
    {
        Try("no such member",
            delegate { dynamic d = "s"; d.Foo(); });
        Try("wrong count",
            delegate { dynamic d = "s"; d.Substring(1, 2, 3); });
        Try("wrong type",
            delegate { dynamic d = "s"; d.Substring("x"); });
        Try("null receiver",
            delegate { dynamic d = null; d.Foo(); });
        Try("private member",
            delegate { dynamic d = new Secret(); d.Hidden(); });
    }
}
