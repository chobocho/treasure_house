// 슬라이드 p15-v14-xm-ref — ref·in·ref readonly 수신자, C# 14
using System;

struct Big { public long A, B, C, D; }

static class BigExt
{
    extension(ref Big b) { public void Bump() => b.A++; }
    extension(in Big b) { public long Total => b.A + b.B + b.C + b.D; }
    extension(ref readonly Big b) { public long Head => b.A; }
#if CLASS
    extension(ref string s) { public int L => s.Length; }
#endif
#if GENERIC
    extension<T>(ref T t) { public void Touch() { } }
#endif
}

class Program
{
    static void Main()
    {
        var big = new Big { A = 1, B = 2, C = 3, D = 4 };
        big.Bump();
        big.Bump();
        Console.WriteLine(big.A + " " + big.Total + " " + big.Head);
        Console.WriteLine(new Big { A = 5 }.Total);    // in: an rvalue
#if RVALUE
        new Big().Bump();                    // ref: needs a variable
#endif
    }
}
