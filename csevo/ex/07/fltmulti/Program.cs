// 슬라이드 p7-v6-filter-multi — 같은 형식의 catch 여럿, C# 6.0
using System;

class Program
{
    static void Run(int code)
    {
        try
        {
            throw new ArgumentException("code", code.ToString());
        }
        catch (ArgumentException e) when (e.ParamName == "1")
        {
            Console.WriteLine("first");
        }
        catch (ArgumentException e) when (e.ParamName != "3")
        {
            Console.WriteLine("second");
        }
        catch (ArgumentException)
        {
            Console.WriteLine("third");
        }
#if BAD
        catch (ArgumentException)
        {
            Console.WriteLine("never");
        }
#endif
    }

    static void Main()
    {
        Run(1);
        Run(2);
        Run(3);
    }
}
