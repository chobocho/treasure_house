// 슬라이드 p3-v2-bool3 — if 에 bool? 를 넣으면, C# 2.0
using System;

class App
{
    static void Main()
    {
        bool? u = null;
        if (u)
        {
            Console.WriteLine("yes");
        }
        bool b = u && true;
        Console.WriteLine(b);
    }
}
