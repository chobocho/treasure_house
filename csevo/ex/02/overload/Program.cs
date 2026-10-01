// 슬라이드 p2-v1-overload — 오버로드 해석의 기초, C# 1.0
using System;
using System.Collections;

class App
{
    static void F(int x)    { Console.WriteLine("F(int)"); }
    static void F(long x)   { Console.WriteLine("F(long)"); }
    static void F(double x) { Console.WriteLine("F(double)"); }
    static void F(object x) { Console.WriteLine("F(object)"); }
    static void F(string x) { Console.WriteLine("F(string)"); }

    static void Main()
    {
        byte b = 1; short s = 1; float f = 1;
        Console.Write("1      -> "); F(1);
        Console.Write("1L     -> "); F(1L);
        Console.Write("byte   -> "); F(b);
        Console.Write("short  -> "); F(s);
        Console.Write("'a'    -> "); F('a');
        Console.Write("float  -> "); F(f);
        Console.Write("1m     -> "); F(1m);
        Console.Write("null   -> "); F(null);
        Console.Write("list   -> "); F(new ArrayList());
        Console.Write("uint   -> "); F(1u);
    }
}
