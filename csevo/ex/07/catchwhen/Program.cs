// 슬라이드 p7-v6-filter-notype — 형식 없는 catch 에 필터, C# 6.0
using System;

class Program
{
    static void Run(int n)
    {
        try
        {
            if (n == 0) throw new DivideByZeroException();
            throw new FormatException();
        }
        catch when (n == 0)
        {
            Console.WriteLine(n + ": caught without a type");
        }
        catch (Exception e)
        {
            Console.WriteLine(n + ": typed " + e.GetType().Name);
        }
    }

    static void Main()
    {
        Run(0);
        Run(1);
    }
}
