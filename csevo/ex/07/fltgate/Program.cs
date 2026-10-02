// 슬라이드 p7-v6-filter — 예외 필터 when, C# 6.0
using System;

class Program
{
    static void Fetch(int status)
    {
        throw new InvalidOperationException("HTTP " + status);
    }

    static void Try(int status)
    {
        try
        {
            Fetch(status);
        }
        catch (InvalidOperationException e)
            when (e.Message.EndsWith("404"))
        {
            Console.WriteLine("not found");
        }
        catch (InvalidOperationException e)
        {
            Console.WriteLine("other: " + e.Message);
        }
    }

    static void Main()
    {
        Try(404);
        Try(500);
    }
}
