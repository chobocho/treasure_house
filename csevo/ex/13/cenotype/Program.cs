// 슬라이드 p13-v12-ce-notype — 자연 형식이 없다, C# 12
using System;
using System.Linq;

class Program
{
    static void Main()
    {
#if BAD
        var x = [1, 2, 3];
#endif
#if BAD2
        int n = [1, 2, 3].Length;
#endif
#if BAD3
        int s = [1, 2, 3].Sum();
#endif
#if SUM
        int t2 = Enumerable.Sum([1, 2, 3]);
#endif
        var y = (int[])[1, 2, 3];       // a cast gives the target
        int t = Enumerable.Sum((int[])[1, 2, 3]);
        Console.WriteLine(y.GetType().Name + " " + t);
    }
}
