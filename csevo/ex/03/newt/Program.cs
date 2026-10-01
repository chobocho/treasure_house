// 슬라이드 p3-v2-new-t — new T() 가 던지는 예외, C# 2.0
using System;

class Boom
{
    public Boom()
    {
        throw new InvalidOperationException("ctor failed");
    }
}

class App
{
    static T Make<T>() where T : new()
    {
        return new T();
    }

    static void Show(string what, Exception e)
    {
        Console.WriteLine(what + ": " + e.GetType().Name);
    }

    static void Main()
    {
        try { new Boom(); }
        catch (Exception e) { Show("new Boom()", e); }
        try { Make<Boom>(); }
        catch (Exception e)
        {
            Show("new T()", e);
            Show("  inner", e.InnerException);
        }
    }
}
