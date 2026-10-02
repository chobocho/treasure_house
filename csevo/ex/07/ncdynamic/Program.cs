// 슬라이드 p7-v6-nullcond-dynamic — dynamic 받는 쪽, C# 6.0
using System;

class App
{
    static void Main()
    {
        dynamic d = "hello";
        Console.WriteLine(d?.Length);
        Console.WriteLine(d?.ToUpper()?.Substring(1, 2));
        d = null;
        Console.WriteLine("[" + d?.Length + "]");
        d = 5;
        try
        {
            Console.WriteLine(d?.Length);       // bound at run time
        }
        catch (Exception e)
        {
            Console.WriteLine(e.GetType().Name);
        }
    }
}
