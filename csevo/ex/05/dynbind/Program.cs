// 슬라이드 p5-v4-dyn-bindtime — 바인딩 시점, C# 4.0
using System;

class Program
{
    static void Show(int i) { Console.WriteLine("int    " + i); }
    static void Show(object o) { Console.WriteLine("object " + o); }

    static void Main()
    {
        object o = 5;
        dynamic d = 5;
        Show(5);    // compile time: Show(int)
        Show(o);    // compile time: Show(object)
        Show(d);    // run time: the value is an int
        d = "five";
        Show(d);    // run time: the value is a string
    }
}
