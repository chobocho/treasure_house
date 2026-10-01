// 슬라이드 p2-v1-usinglower — using 을 풀어 쓰면, C# 1.0
using System;

class Res : IDisposable
{
    public void Dispose() { Console.WriteLine("  dispose"); }
}

class App
{
    static Res Find(bool found) { return found ? new Res() : null; }

    static void Main()
    {
        Console.WriteLine("using with null:");
        using (Res r = Find(false))      // no NullReferenceException
        {
            Console.WriteLine("  body, r is null: " + (r == null));
        }

        Console.WriteLine("the same, by hand:");
        Res h = Find(true);
        try
        {
            Console.WriteLine("  body");
        }
        finally
        {
            if (h != null) ((IDisposable)h).Dispose();
        }
    }
}
