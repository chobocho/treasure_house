// 슬라이드 p2-v1-finallyret — return 뒤에도 finally 는 돈다, C# 1.0
using System;
using System.Text;

class App
{
    static int Number()
    {
        int x = 1;
        try
        {
            return x;                    // the value 1 is taken here
        }
        finally
        {
            x = 99;                      // too late for the result
            Console.WriteLine("finally: x = " + x);
        }
    }

    static StringBuilder Builder()
    {
        StringBuilder sb = new StringBuilder("a");
        try { return sb; }
        finally { sb.Append("b"); }      // same object: visible
    }

    static void Main()
    {
        Console.WriteLine("Number()  = " + Number());
        Console.WriteLine("Builder() = " + Builder());
    }
}
