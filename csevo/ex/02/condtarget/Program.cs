// 슬라이드 p2-v1-condfail — 대상 형식이 있으면 받아 주는 조건식, C# 9
using System;

class App
{
    static void Main()
    {
        bool yes = true;
        object o = yes ? 1 : null;                   // target: object
        object p = !yes ? 1 : "one";
        Console.WriteLine(o + " " + p);
    }
}
