// 슬라이드 p1-design-exc-cs — 같은 프로그램, 검사 예외 없이, C# 1.0
using System;
using System.IO;

class Program
{
    static string Load(string path)
    {
        throw new IOException("cannot open " + path);
    }

    static void Step()
    {
        try
        {
            Console.WriteLine(Load("a.txt"));
        }
        finally
        {
            Console.WriteLine("cleanup in Step"); // protect only
        }
    }

    static void Main()
    {
        try
        {
            Step();                    // like the main message loop
        }
        catch (Exception e)
        {
            Console.WriteLine("handler: " + e.Message);
        }
    }
}
