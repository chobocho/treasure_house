// 슬라이드 p3-v2-foreach-cast — foreach 의 숨은 캐스트, C# 2.0
using System;
using System.Collections;

class App
{
    static IEnumerable Mixed()
    {
        yield return "a";
        yield return 2;                   // object: nothing stops this
    }

    static void Main()
    {
        try
        {
            foreach (string s in Mixed()) // a hidden (string) cast
            {
                Console.WriteLine(s);
            }
        }
        catch (InvalidCastException e)
        {
            Console.WriteLine(e.GetType().Name);
        }
    }
}
