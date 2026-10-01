// 슬라이드 p4-v3-query-syntactic — 패턴이 없는 형식에 쿼리 식, C# 3.0
using System;

class Bag { }            // no Select at all

class OnlySelect         // Select, but no Where
{
    public OnlySelect Select(Func<int, int> f) { return this; }
}

class Program
{
    static void Main()
    {
        object a = from x in new Bag() select x;
        object b = from x in new OnlySelect()
                   where x > 1
                   select x;
    }
}
