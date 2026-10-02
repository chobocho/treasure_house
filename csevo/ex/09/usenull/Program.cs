// 슬라이드 p9-v8-ud-null — null 과 예외, C# 8.0
using System;

class Res : IDisposable
{
    public void Dispose() => Console.WriteLine("  dispose");
}

class App
{
    static Res Maybe(bool yes) => yes ? new Res() : null;

    static void Body(bool yes)
    {
        using var r = Maybe(yes);     // null: no Dispose, no exception
        Console.WriteLine("  body, r is null: " + (r == null));
        if (yes) throw new InvalidOperationException("boom");
    }

    static void Main()
    {
        Body(false);
        try { Body(true); }
        catch (InvalidOperationException e)
        {
            Console.WriteLine("caught " + e.Message + " after dispose");
        }
    }
}
