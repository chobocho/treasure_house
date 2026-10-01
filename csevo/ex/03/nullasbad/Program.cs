// 슬라이드 p3-v2-nullable-as — int 에는 as 를 못 쓴다, C# 2.0
using System;

class App
{
    static void Main()
    {
        object o = 5;
        int n = o as int;
        Console.WriteLine(n);
    }
}
