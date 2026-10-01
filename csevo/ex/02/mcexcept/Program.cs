// 슬라이드 p2-v1-mcexcept — 하나가 던지면 나머지는 안 불린다, C# 1.0
using System;

delegate void Handler();

class App
{
    static void First() { Console.WriteLine("  First"); }
    static void Broken() { throw new ApplicationException("boom"); }
    static void Last() { Console.WriteLine("  Last"); }

    static void Report(Exception e)
    {
        Console.WriteLine("  caught " + e.Message);
    }

    static void Main()
    {
        Handler h = new Handler(First);
        h += new Handler(Broken);
        h += new Handler(Last);

        Console.WriteLine("h():");
        try { h(); }
        catch (Exception e) { Report(e); }

        Console.WriteLine("one by one:");
        foreach (Handler one in h.GetInvocationList())
        {
            try { one(); }
            catch (Exception e) { Report(e); }
        }
    }
}
