// 슬라이드 p7-v6-filter-pattern — 필터 안의 패턴, C# 7.0
using System;

class Program
{
    static void Run(Exception ex)
    {
        try
        {
            throw ex;
        }
        catch (Exception e) when (e is ArgumentException a
                                  && a.ParamName == "id")
        {
            Console.WriteLine("bad id: " + a.ParamName);
        }
        catch (Exception e)
        {
            Console.WriteLine("other: " + e.GetType().Name);
        }
    }

    static void Main()
    {
        Run(new ArgumentException("x", "id"));
        Run(new ArgumentException("x", "name"));
    }
}
