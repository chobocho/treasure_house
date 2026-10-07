// 슬라이드 p15-v14-brk-enum — 버린 열거자는 다시 돌지 않는다, C# 14
using System;
using System.Collections.Generic;

class Program
{
    static IEnumerator<int> Numbers()
    {
        yield return 1;
        Console.Write("[not executed after disposal] ");
        yield return 2;
    }

    static void Main()
    {
        IEnumerator<int> e = Numbers();
        Console.WriteLine(e.MoveNext() + " " + e.Current);
        e.Dispose();
        Console.WriteLine(e.MoveNext() + " " + e.Current);
    }
}
