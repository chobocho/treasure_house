// 슬라이드 p2-v1-pinvoke — DllImport 로 C 함수 부르기, C# 1.0
using System;
using System.Runtime.InteropServices;

class LibC
{
    [DllImport("libc")]
    public static extern int abs(int n);

    [DllImport("libc")]
    public static extern int atoi(string s);      // passed as a char*
}

class App
{
    static void Main()
    {
        Console.WriteLine("abs(-42)    = " + LibC.abs(-42));
        Console.WriteLine("atoi(\"77\")  = " + LibC.atoi("77"));
        Console.WriteLine("atoi(\"9x\")  = " + LibC.atoi("9x"));
    }
}
