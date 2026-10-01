// 슬라이드 p4-v3-et-convert — 컴파일러가 넣은 것이 보인다, C# 3.0
using System;
using System.Linq.Expressions;

class Program
{
    static void Main()
    {
        Expression<Func<int, long>> widen = x => x;
        Expression<Func<int, double>> mixed = x => x / 2 + 0.5;
        Expression<Func<int?, bool>> lifted = x => x > 1;
        Expression<Func<int, bool>> folded = x => x > 60 * 60;
        Expression<Func<int, int>> chk = x => checked(x + 1);

        Console.WriteLine(widen);
        Console.WriteLine(mixed);
        Console.WriteLine(lifted);
        Console.WriteLine(folded);
        Console.WriteLine(chk + "   body: " + chk.Body.NodeType);
    }
}
