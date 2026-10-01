// 슬라이드 p4-v3-query-escape — 쿼리 안에서는 @ 를 붙여야, C# 3.0
using System;
using System.Linq;

class Program
{
    static void Main()
    {
        int where = 2;
        int[] into = { 1, 2, 3 };
        int[] big = (from @from in @into
                     where @from > @where
                     select @from * 10).ToArray();
        Console.WriteLine(big[0]);
    }
}
