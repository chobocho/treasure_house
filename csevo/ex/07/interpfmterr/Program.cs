// 슬라이드 p7-v6-interp-why — string.Format 의 번호 실수, C# 6.0
using System;

class App
{
    static void Try(string format, params object[] args)
    {
        try
        {
            Console.WriteLine("ok:   " + string.Format(format, args));
        }
        catch (FormatException e)
        {
            Console.WriteLine("fail: " + e.Message);
        }
    }

    static void Main()
    {
        string name = "Ada";
        int items = 3;
        Try("{0} bought {1} items", name, items);
        Try("{0} bought {2} items", name, items);  // wrong index
        Try("{0} bought {1} items", name);         // missing argument
        Try("{0} bought items", name, items);      // extra argument
        Try("{0} bought {1 items", name, items);   // broken brace
    }
}
