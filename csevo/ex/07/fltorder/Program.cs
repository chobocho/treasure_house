// 슬라이드 p7-v6-filter-order — 필터는 안쪽 finally 보다 먼저, C# 6.0
using System;

class Program
{
    static bool Check(string who)
    {
        Console.WriteLine("  " + who + " decides");
        return true;
    }

    static void Inner()
    {
        try
        {
            throw new InvalidOperationException();
        }
        finally
        {
            Console.WriteLine("  inner finally");
        }
    }

    static void Main()
    {
        Console.WriteLine("filter:");
        try { Inner(); }
        catch (Exception) when (Check("filter"))
        {
            Console.WriteLine("  catch body");
        }

        Console.WriteLine("catch, then decide:");
        try { Inner(); }
        catch (Exception)
        {
            if (!Check("catch body")) throw;
        }
    }
}
