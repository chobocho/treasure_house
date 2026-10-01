// 슬라이드 p4-v3-query-keywords — 쿼리 낱말을 이름으로 쓴 코드, C# 1.0
using System;

class Program
{
    static int select(int from, int where)
    {
        return from * where;
    }

    static void Main()
    {
        int from = 3, where = 4;
        int group = select(from, where);
        int[] into = { from, where, group };
        Console.WriteLine("group = " + group + ", into " + into.Length);
    }
}
