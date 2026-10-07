// 슬라이드 p15-v14-et-order — 순서를 바꾼 명명 인수, C# 14
using System;
using System.Linq.Expressions;

class Program
{
    static int Log(string s, int v)
    {
        Console.Write(s + " ");
        return v;
    }

    public static int Sub(int a, int b) => a - b;

    static void Main()
    {
        Func<int> f = () => Sub(b: Log("b", 1), a: Log("a", 5));
        Console.WriteLine("= " + f());          // written order: b, a

        Expression<Func<int>> t =
            () => Sub(a: Log("a", 5), b: Log("b", 1));
        Console.WriteLine(t.Body);
        Console.WriteLine("= " + t.Compile()());
#if SWAP
        Expression<Func<int>> u =
            () => Sub(b: Log("b", 1), a: Log("a", 5));
#endif
    }
}
