// 슬라이드 p8-v7_2-in-over — 값과 in 의 오버로드, C# 7.2
using System;

struct Big
{
    public long A;
    public Big(long a) { A = a; }
}

class App
{
    static void M(Big b)    { Console.WriteLine("M(Big)"); }
    static void M(in Big b) { Console.WriteLine("M(in Big)"); }

    static void Main()
    {
        var x = new Big(1);
        M(x);            // no modifier
        M(in x);         // in at the call site
        M(new Big(2));   // an rvalue
    }
}
