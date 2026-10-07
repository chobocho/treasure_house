// 슬라이드 p15-v14-xm-using — using static 이 들여오는 것, C# 14
using System;
using static Tools.E;

namespace Tools
{
    static class E
    {
        extension(object o)
        {
            public string Who() => "instance " + o;
            public static string Hello() => "static";
            public static int Answer { get => 42; }
        }
    }
}

class Program
{
    static void Main()
    {
        Console.WriteLine(Hello() + " " + get_Answer());   // static
        Console.WriteLine(object.Hello() + " " + 5.Who());
        Console.WriteLine(Tools.E.Who(5));
#if BAD
        Console.WriteLine(Who(5));                     // not imported
#endif
    }
}
