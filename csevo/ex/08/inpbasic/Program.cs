// 슬라이드 p8-v7_2-in — in 매개변수, C# 7.2
using System;

struct Big
{
    public long A, B, C, D;
    public Big(long a) { A = a; B = a * 2; C = a * 3; D = a * 4; }
}

class App
{
    // passed by reference, but the callee may not write it
    static long Sum(in Big b)
    {
        return b.A + b.B + b.C + b.D;
    }

    static void Main()
    {
        var x = new Big(1);
        Console.WriteLine(Sum(in x));        // in at the call site
        Console.WriteLine(Sum(x));           // in may be left out
        Console.WriteLine(Sum(new Big(2)));  // an rvalue: a hidden temp
        Console.WriteLine(Sum(default));     // the default literal too
    }
}
