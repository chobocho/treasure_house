// 슬라이드 p15-v14-et-why — 제안서의 Contains 예, C# 14
using System;
using System.Linq;
using System.Linq.Expressions;

class Program
{
    static void Main()
    {
        Expression<Func<int?[], int, bool>> e;
        e = (a, i) => a.Contains(i);
        Console.WriteLine(e.Body);
        e = (a, i) => a.Contains(i, comparer: null);
        Console.WriteLine(e.Body);
        Console.WriteLine(e.Compile()([1, 2, null], 2));
    }
}
