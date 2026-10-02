// 슬라이드 p7-v6-filter-log — 잡지 않고 기록만 하는 필터, C# 6.0
using System;

class Program
{
    static bool Log(Exception e)
    {
        Console.WriteLine("log: " + e.Message);
        return false;                 // never catch
    }

    static void Work()
    {
        try
        {
            throw new FormatException("bad input");
        }
        catch (Exception e) when (Log(e))
        {
            Console.WriteLine("unreachable");
        }
    }

    static void Main()
    {
        try
        {
            Work();
        }
        catch (FormatException e)
        {
            Console.WriteLine("handled in Main: " + e.Message);
        }
    }
}
