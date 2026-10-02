// 슬라이드 p5-v4-dyn-nullarg — null 인 dynamic 인자, C# 4.0
using System;

class Program
{
    static void Show(object o) { Console.WriteLine("Show(object)"); }
    static void Show(string s) { Console.WriteLine("Show(string)"); }

    static void Main()
    {
        dynamic d = "text";
        Show(d);
        d = 1;
        Show(d);
        d = null;
        Show(d);
        Show(null);
    }
}
