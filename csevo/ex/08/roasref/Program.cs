// 슬라이드 p8-v7_2-rostruct-copy — Unsafe.AsRef(in …), C# 7.2
using System;
using System.Runtime.CompilerServices;

class App
{
    static void Main()
    {
        int a = 1;
        ref int r = ref Unsafe.AsRef(in a);
        Console.WriteLine(r);
    }
}
