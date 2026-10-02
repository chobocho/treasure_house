// 슬라이드 p10-v9-lfa-extern — extern 지역 함수, C# 9.0
using System;
using System.Runtime.InteropServices;

class App
{
    static void Main()
    {
        Console.WriteLine(abs(-42));

        [DllImport("libc")]
        static extern int abs(int x);            // no body: ';'
    }
}
