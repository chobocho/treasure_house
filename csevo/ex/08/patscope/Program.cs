// 슬라이드 p8-v7-pat-scope — 패턴 변수는 바깥 블록까지 산다, C# 7.0
using System;

class App
{
    static void Show(object o)
    {
        if (!(o is int n))              // n's scope: the method body
        {
            Console.WriteLine("not an int");
            return;
        }
        Console.WriteLine(n + 1);           // definitely assigned here
    }

    static void Main()
    {
        Show(41);
        Show("x");
        object o = 7;
        bool ok = o is int k && k > 5;      // a declaration statement
        k = 100;                            // k is in scope here too
        Console.WriteLine(ok + " " + k);
        while (o is int m && m < 9)
            o = m + 1;                      // m: the while only
        Console.WriteLine(o);
    }
}
