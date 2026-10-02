// 슬라이드 p7-v6-filter-throw — 필터 안에서 난 예외, C# 6.0
using System;

class Program
{
    static bool Broken(Exception e)
    {
        Console.WriteLine("filter runs");
        string s = null;
        return s.Length > 0;          // NullReferenceException here
    }

    static void Main()
    {
        try
        {
            try
            {
                throw new TimeoutException("slow");
            }
            catch (Exception e) when (Broken(e))
            {
                Console.WriteLine("inner catch");
            }
        }
        catch (Exception e)
        {
            Console.WriteLine("outer: " + e.GetType().Name);
        }
    }
}
