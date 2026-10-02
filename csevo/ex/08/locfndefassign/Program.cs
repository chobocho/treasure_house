// 슬라이드 p8-v7-locfn-defassign — 호출하는 자리마다 확정 대입, C# 7.0
using System;

class App
{
    static void Main()
    {
        int x;
        Console.WriteLine(Show());      // x not assigned yet
        x = 1;
        Console.WriteLine(Show());      // fine here

        int Show() => x * 10;
    }
}
