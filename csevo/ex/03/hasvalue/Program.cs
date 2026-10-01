// 슬라이드 p3-v2-hasvalue — HasValue·Value·GetValueOrDefault, C# 2.0
using System;

class App
{
    static void Main()
    {
        int? none = null;
        Console.WriteLine(none.HasValue);
        Console.WriteLine(none.GetValueOrDefault());
        Console.WriteLine(none.GetValueOrDefault(9));
        try
        {
            int x = none.Value;           // unwrapping a null
            Console.WriteLine(x);
        }
        catch (InvalidOperationException e)
        {
            Console.WriteLine(e.Message);
        }
        try
        {
            int y = (int)none;            // the cast is .Value too
            Console.WriteLine(y);
        }
        catch (InvalidOperationException e)
        {
            Console.WriteLine(e.GetType().Name);
        }
    }
}
