// 슬라이드 p2-v1-finallyexc — finally 가 던지면 원래 예외는, C# 1.0
using System;

class App
{
    static void Work()
    {
        try
        {
            throw new InvalidOperationException("the real problem");
        }
        finally
        {
            Console.WriteLine("cleanup fails too");
            throw new ObjectDisposedException("log");   // replaces it
        }
    }

    static void Main()
    {
        try { Work(); }
        catch (Exception e)
        {
            Console.WriteLine("caught: " + e.GetType().Name);
            Console.WriteLine("inner:  " + (e.InnerException == null
                ? "none" : e.InnerException.Message));
        }
    }
}
