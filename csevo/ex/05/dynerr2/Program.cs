// 슬라이드 p5-v4-dyn-binderex-type — 예외의 정체, C# 4.0
using System;

class Program
{
    static void Main()
    {
        dynamic d = 42;
        try
        {
            d.Missing = 1;
        }
        catch (Exception e)
        {
            Type t = e.GetType();
            while (t != null)
            {
                Console.WriteLine(t.FullName + "  [" +
                                  t.Assembly.GetName().Name + "]");
                t = t.BaseType;
            }
        }
        d.Missing = 2;     // unhandled
    }
}
