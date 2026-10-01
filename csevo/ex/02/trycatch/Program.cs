// 슬라이드 p2-v1-trycatch — try·catch·finally 의 순서, C# 1.0
using System;

class App
{
    static void Inner(int mode)
    {
        try
        {
            Console.WriteLine("  inner try");
            if (mode == 1) throw new FormatException("bad input");
            if (mode == 2) throw new ArgumentException("bad arg");
        }
        catch (FormatException e)
        {
            Console.WriteLine("  inner catch: " + e.Message);
        }
        finally
        {
            Console.WriteLine("  inner finally");
        }
        Console.WriteLine("  after inner try");
    }

    static void Main()
    {
        for (int mode = 0; mode <= 2; mode++)
        {
            Console.WriteLine("mode " + mode + ":");
            try { Inner(mode); }
            catch (Exception e)
            {
                Console.WriteLine("  outer catch: " + e.GetType().Name);
            }
        }
    }
}
