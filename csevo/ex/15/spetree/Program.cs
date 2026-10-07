// 슬라이드 p15-v14-sp-etree — 식 트리 안의 스팬 판, C# 14
using System;
using System.Linq;
using System.Linq.Expressions;

class Program
{
    static void Run(Expression<Func<int[], int, bool>> e)
    {
        Console.WriteLine(e);
        try
        {
            var f = e.Compile(preferInterpretation: true);
            Console.WriteLine("  interpreted: " + f([1, 2], 2));
        }
        catch (ArgumentException x)
        {
            Console.WriteLine("  " + x.GetType().Name);
        }
    }

    static void Main()
    {
        Run((array, num) => array.Contains(num));
        Run((array, num) => Enumerable.Contains(array, num));
    }
}
