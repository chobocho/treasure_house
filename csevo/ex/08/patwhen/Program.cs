// 슬라이드 p8-v7-pat-when — when 은 위에서부터 차례로, C# 7.0
using System;

class App
{
    static bool Check(string name, bool result)
    {
        Console.WriteLine("  when " + name);
        return result;
    }

    static void M(object o)
    {
        switch (o)
        {
            case int n when Check("n > 10", n > 10):
                Console.WriteLine("big"); break;
            case int n when Check("n > 0", n > 0):
                Console.WriteLine("positive"); break;
            case string s when Check("s", true):
                Console.WriteLine("string"); break;
            case int n:
                Console.WriteLine("other int"); break;
        }
    }

    static void Main()
    {
        Console.WriteLine("M(5):"); M(5);
        Console.WriteLine("M(-1):"); M(-1);
        Console.WriteLine("M(\"a\"):"); M("a");
    }
}
