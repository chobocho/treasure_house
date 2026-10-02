// 슬라이드 p10-v9-fnptr-limits — 함수 포인터가 못 하는 것, C# 9.0
using System;
using System.Collections.Generic;

unsafe class App
{
    int Instance(int x) => x;
    static int Log(int x) => x;
    static string Log(string s) => s;

    static void Main()
    {
        delegate*<int, int> pi = &Log;          // overload by signature
        delegate*<string, string> ps = &Log;
        Console.WriteLine(pi(7) + " " + ps("seven"));
#if BAD
        App a = new App();
        delegate*<int, int> f1 = &a.Instance;   // instance method
        object o = pi;                          // to object
        var list = new List<delegate*<int, int>>();
#endif
    }
}
