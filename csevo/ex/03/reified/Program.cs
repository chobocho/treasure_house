// 슬라이드 p3-v2-reified — 형식 인자는 실행 중에도 남는다, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static string Name<T>(T x)
    {
        return typeof(T).Name;            // the T of this call
    }

    static T Cast<T>(object o)
    {
        return (T)o;                      // checked at run time
    }

    static void Main()
    {
        object o = new List<int>();
        Console.WriteLine(o is List<int>);
        Console.WriteLine(o is List<string>);
        Console.WriteLine(Name(42) + " " + Name("s"));
        Console.WriteLine(Name<object>("s"));
        Console.WriteLine(Cast<int>(5));
        try
        {
            Cast<string>(5);
        }
        catch (InvalidCastException e)
        {
            Console.WriteLine(e.GetType().Name);
        }
    }
}
