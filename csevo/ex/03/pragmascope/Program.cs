// 슬라이드 p3-v2-pragma-scope — 끄는 범위, C# 2.0
using System;

class App
{
    static void Main()
    {
#pragma warning disable CS0168
        int a;                           // off: by code with "CS"
#pragma warning restore CS0168
#pragma warning disable
        int b;                           // off: no list = all
#pragma warning restore
        int c;                           // on again: warned
        Console.WriteLine("ok");
    }
}
