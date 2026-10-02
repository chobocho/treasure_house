// 슬라이드 p5-v4-dyn-subexpr — dynamic 아닌 인자는 정적 형식, C# 4.0
using System;

class Program
{
    static void P(object a, object b) { Console.WriteLine("obj obj"); }
    static void P(string a, object b) { Console.WriteLine("str obj"); }
    static void P(object a, string b) { Console.WriteLine("obj str"); }
    static void P(string a, string b) { Console.WriteLine("str str"); }

    static void Main()
    {
        object x = "x";
        dynamic y = "y";
        P(x, x);
        P(x, y);
        P((dynamic)x, y);
    }
}
