// 슬라이드 p2-v1-cctorfail — 정적 생성자가 던지면, C# 1.0
using System;

class Table
{
    public static int Size = 8;
    static Table()
    {
        Console.WriteLine("static constructor runs");
        throw new InvalidOperationException("config missing");
    }
}

class App
{
    static void Main()
    {
        for (int i = 1; i <= 2; i++)
        {
            try
            {
                Console.WriteLine("try " + i + ": " + Table.Size);
            }
            catch (Exception e)
            {
                Console.WriteLine("try " + i + ": " + e.GetType().Name
                    + " <- " + e.InnerException.Message);
            }
        }
    }
}
