// 슬라이드 p2-v1-sizeof — 내장 형식의 sizeof 는 상수, C# 1.0
using System;

enum Small : byte { A }

class App
{
    const int IntBytes = sizeof(int);              // a constant

    static void Main()
    {
        Console.WriteLine("byte    " + sizeof(byte));
        Console.WriteLine("char    " + sizeof(char));
        Console.WriteLine("bool    " + sizeof(bool));
        Console.WriteLine("int     " + IntBytes);
        Console.WriteLine("long    " + sizeof(long));
        Console.WriteLine("double  " + sizeof(double));
        Console.WriteLine("decimal " + sizeof(decimal));
        Console.WriteLine("Small   " + sizeof(Small));
    }
}
